"""Slicer — computes filament weight and print time from a 3D model URL.

Priority order:
  1. BambuStudio CLI  — if BAMBU_STUDIO_PATH set and binary exists. Works on macOS.
                        Uses real toolpath planning → accurate weight + time.
                        Also exports STL for the 3D viewer.
  2. OrcaSlicer CLI   — if ORCA_SLICER_PATH set (Linux VPS only; segfaults on macOS).
  3. trimesh volume   — downloads OBJ/STL, computes mesh volume. Decent approximation.
  4. Dimension guess  — last resort if all else fails.
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

BAMBU_STUDIO_PATH = os.getenv(
    "BAMBU_STUDIO_PATH",
    "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio",
)
BAMBU_PRINTER_MODEL = os.getenv("BAMBU_PRINTER_MODEL", "A1")  # A1, P1S, X1C, A1M …
ORCA_SLICER_PATH = os.getenv(
    "ORCA_SLICER_PATH",
    "/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer",
)

_BAMBU_PROFILES = Path("/Applications/BambuStudio.app/Contents/resources/profiles/BBL")
_ORCA_PROFILES  = Path("/Applications/OrcaSlicer.app/Contents/resources/profiles/BBL")

# Support settings requested by client (Bambu tree support, 0.276 Z distance)
_SUPPORT_SETTINGS: dict = {
    "from": "",
    "enable_support":                "1",
    "support_type":                  "tree(auto)",
    "support_top_z_distance":        "0.276",
    "support_bottom_z_distance":     "0.276",
    "support_interface_top_layers":  "3",
}

_PLA_DENSITY_G_PER_CM3 = 1.24
_INFILL_FACTOR         = 0.20
_WALL_FACTOR           = 0.08
_PRINT_SPEED_G_PER_MIN = 0.45


@dataclass(frozen=True)
class SliceResult:
    grams: float
    print_hours: float
    tmf_path: str | None   # .3mf path (BambuStudio/Orca) or None
    stl_path: str | None   # STL path for the 3D viewer, or None


def slice_model(
    model_url: str,
    material: str = "PLA",
    dimensions_hint: str = "",
) -> SliceResult:
    if ORCA_SLICER_PATH and Path(ORCA_SLICER_PATH).exists():
        try:
            return _slice_with_orca(model_url, material, dimensions_hint)
        except Exception as exc:
            logger.warning("OrcaSlicer failed (%s) — falling back to trimesh", exc)

    return _slice_with_trimesh(model_url, dimensions_hint)


# ── BambuStudio CLI ───────────────────────────────────────────────────────────

def _bambu_profile_paths(printer: str) -> tuple[list[str], str | None]:
    """Return (settings_json_list, filament_json_or_None) for the given printer model."""
    process  = _BAMBU_PROFILES / "process"  / f"0.20mm Standard @BBL {printer}.json"
    machine  = _BAMBU_PROFILES / "machine"  / f"Bambu Lab {printer} 0.4 nozzle.json"
    filament = _BAMBU_PROFILES / "filament" / f"Bambu PLA Basic @BBL {printer}.json"

    if not process.exists():
        raise RuntimeError(f"No BambuStudio process profile for printer '{printer}': {process}")

    settings: list[str] = []
    if machine.exists():
        settings.append(str(machine))
    settings.append(str(process))

    return settings, str(filament) if filament.exists() else None


def _slice_with_bambu(model_url: str, material: str) -> SliceResult:
    try:
        import trimesh  # type: ignore
    except ImportError:
        raise RuntimeError("trimesh required for OBJ → STL conversion before BambuStudio slice")

    with tempfile.TemporaryDirectory() as raw_tmpdir:
        tmpdir = Path(raw_tmpdir)

        # 1. Download model
        response = httpx.get(model_url, timeout=30.0)
        response.raise_for_status()
        url_lower = model_url.lower().split("?")[0]
        suffix = ".obj" if url_lower.endswith(".obj") else ".stl"
        model_in = tmpdir / f"model{suffix}"
        model_in.write_bytes(response.content)

        # 2. Convert OBJ → STL (BambuStudio handles STL more reliably headlessly)
        stl_path = tmpdir / "model.stl"
        if suffix == ".obj":
            mesh = trimesh.load(str(model_in), force="mesh")
            mesh.export(str(stl_path))
        else:
            stl_path = model_in

        # 3. Write support-settings override JSON
        override_path = tmpdir / "support_override.json"
        override_path.write_text(json.dumps(_SUPPORT_SETTINGS))

        settings_list, filament_path = _bambu_profile_paths(BAMBU_PRINTER_MODEL)
        settings_list.append(str(override_path))

        output_dir = tmpdir / "output"
        output_dir.mkdir()
        output_3mf = tmpdir / "output.3mf"

        cmd = [
            BAMBU_STUDIO_PATH,
            "--slice", "0",
            "--load-settings", ";".join(settings_list),
            "--outputdir", str(output_dir),
            "--export-3mf", str(output_3mf),
            str(stl_path),
        ]
        if filament_path:
            cmd.extend(["--load-filaments", filament_path])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        combined = result.stdout + result.stderr
        logger.info("BambuStudio output:\n%s", combined[:1200])

        if result.returncode != 0:
            raise RuntimeError(f"BambuStudio exited {result.returncode}: {combined[:400]}")

        grams, hours = _parse_slicer_stdout(combined)
        if grams == 0.0:
            raise RuntimeError("BambuStudio produced no weight data — output unparseable")

        # Persist STL outside the temp dir so /model.stl can serve it
        persistent_stl = _persist_stl(stl_path)
        tmf = str(output_3mf) if output_3mf.exists() else None

        grams = round(max(5.0, min(300.0, grams)), 1)
        hours = round(max(0.25, min(24.0, hours)), 2)
        logger.info("BambuStudio — %.1fg, %.2fh", grams, hours)
        return SliceResult(grams=grams, print_hours=hours, tmf_path=tmf, stl_path=persistent_stl)


# ── OrcaSlicer CLI ────────────────────────────────────────────────────────────

def _orca_profile_args() -> list[str]:
    """Return --load-settings and --load-filaments args if BBL A1 profiles exist."""
    process  = _ORCA_PROFILES / "process"  / "0.20mm Standard @BBL A1.json"
    machine  = _ORCA_PROFILES / "machine"  / "Bambu Lab A1 0.4 nozzle.json"
    filament = _ORCA_PROFILES / "filament" / "Bambu PLA Basic @BBL A1.json"
    args: list[str] = []
    if process.exists() and machine.exists():
        args += ["--load-settings", f"{machine};{process}"]
    if filament.exists():
        args += ["--load-filaments", str(filament)]
    return args


def _parse_orca_gcode(gcode_path: Path) -> tuple[float, float]:
    """Extract grams and hours from an OrcaSlicer gcode file."""
    grams = 0.0
    hours = 0.0
    text = gcode_path.read_text(errors="ignore")

    # filament used [cm3] → grams via PLA density
    cm3_match = re.search(r"filament used \[cm3\]\s*=\s*([0-9.]+)", text)
    if cm3_match:
        grams = float(cm3_match.group(1)) * _PLA_DENSITY_G_PER_CM3

    # total estimated time: 7m 44s  OR  1h 23m 5s
    time_match = re.search(
        r"total estimated time:\s*(?:(\d+)h\s*)?(?:(\d+)m\s*)?(?:(\d+)s)?", text
    )
    if time_match:
        h = int(time_match.group(1) or 0)
        m = int(time_match.group(2) or 0)
        s = int(time_match.group(3) or 0)
        hours = h + m / 60 + s / 3600

    return grams, hours


def _parse_target_mm(dimensions_hint: str) -> float | None:
    """Extract the largest dimension from a hint like '10cm tall' → 100.0 mm."""
    nums = re.findall(r"(\d+(?:\.\d+)?)\s*(mm|cm|m)?", dimensions_hint, re.IGNORECASE)
    if not nums:
        return None
    values_mm = []
    for val_str, unit in nums:
        val = float(val_str)
        unit = (unit or "cm").lower()
        if unit == "m":
            val *= 1000
        elif unit == "cm":
            val *= 10
        # mm stays as-is
        values_mm.append(val)
    return max(values_mm) if values_mm else None


def _slice_with_orca(model_url: str, material: str, dimensions_hint: str = "") -> SliceResult:
    with tempfile.TemporaryDirectory() as raw_tmpdir:
        tmpdir = Path(raw_tmpdir)

        # 1. Download model
        response = httpx.get(model_url, timeout=30.0)
        response.raise_for_status()
        url_lower = model_url.lower().split("?")[0]
        suffix = ".obj" if url_lower.endswith(".obj") else ".stl"
        model_in = tmpdir / f"model{suffix}"
        model_in.write_bytes(response.content)

        # 2. Export to STL, scale to requested dimensions, repair normals.
        #    Meshy normalizes models to ~1 unit — OrcaSlicer treats STL units as mm,
        #    so a 1-unit model slices as 1mm (nearly nothing). Scale to actual target size.
        stl_in = tmpdir / "model.stl"
        try:
            import trimesh  # type: ignore
            mesh = trimesh.load(str(model_in), force="mesh")

            # Scale to target dimensions (mm) if we know them
            target_mm = _parse_target_mm(dimensions_hint)
            if target_mm and target_mm > 0:
                current_max = float(max(mesh.bounding_box.extents))
                if current_max > 0:
                    scale = target_mm / current_max
                    mesh.apply_scale(scale)
                    logger.info("Scaled mesh %.4f → %.1fmm (target %.1fmm)", current_max, float(max(mesh.bounding_box.extents)), target_mm)

            target_faces = 60_000
            if len(mesh.faces) > target_faces:
                try:
                    mesh = mesh.simplify_quadric_decimation(target_faces)
                except Exception:
                    pass  # no fast_simplification — use full mesh
            trimesh.repair.fix_normals(mesh)
            trimesh.repair.fix_winding(mesh)
            mesh.export(str(stl_in))
            model_in = stl_in
            logger.info("Mesh ready — watertight=%s, faces=%d", mesh.is_watertight, len(mesh.faces))
        except Exception as repair_exc:
            logger.warning("STL export failed (%s) — using original file", repair_exc)

        output_dir = tmpdir / "output"
        output_dir.mkdir()

        cmd = [
            ORCA_SLICER_PATH,
            "--slice", "0",
            "--outputdir", str(output_dir),
            str(model_in),
        ] + _orca_profile_args()

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=180, check=False,
        )
        combined = result.stdout + result.stderr
        logger.info("OrcaSlicer output:\n%s", combined[:800])

        # Find the gcode file
        gcodes = list(output_dir.glob("*.gcode"))
        if not gcodes:
            raise RuntimeError(f"OrcaSlicer produced no gcode (exit {result.returncode}): {combined[:300]}")

        grams, hours = _parse_orca_gcode(gcodes[0])
        if grams == 0.0:
            raise RuntimeError("OrcaSlicer gcode has no filament data")

        grams = round(max(5.0, min(300.0, grams)), 1)
        hours = round(max(0.25, min(20.0, hours)), 2)

        # Persist STL for viewer
        stl_path = _persist_stl(model_in) if model_in.suffix == ".stl" else None

        logger.info("OrcaSlicer — %.1fg, %.2fh", grams, hours)
        return SliceResult(grams=grams, print_hours=hours, tmf_path=None, stl_path=stl_path)


# ── trimesh volume-based (default) ───────────────────────────────────────────

def _slice_with_trimesh(model_url: str, dimensions_hint: str) -> SliceResult:
    try:
        import trimesh  # type: ignore
    except ImportError:
        logger.warning("trimesh not installed — falling back to dimension estimate")
        return _estimate_from_dimensions(dimensions_hint)

    try:
        response = httpx.get(model_url, timeout=30.0)
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Could not download model (%s) — falling back to dimensions", exc)
        return _estimate_from_dimensions(dimensions_hint)

    url_lower = model_url.lower().split("?")[0]
    suffix = ".obj" if url_lower.endswith(".obj") else ".stl"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    stl_path: str | None = None
    try:
        mesh = trimesh.load(tmp_path, force="mesh")

        # Always persist STL for the viewer — even if volume is unreliable
        stl_path = _persist_stl(Path(tmp_path))

        raw_vol = abs(mesh.volume)

        # Detect unit scale from bounding box — Meshy normalizes models differently per version.
        # Heuristic: if the largest bounding-box dimension is <5, assume meters; else assume mm.
        extents = mesh.bounding_box.extents
        max_extent = float(max(extents)) if len(extents) else 1.0
        if max_extent < 5.0:
            # Meter units — multiply by 1e6 to get cm³
            volume_cm3 = raw_vol * 1_000_000.0
        elif max_extent > 500.0:
            # Millimeter units — divide by 1000 to get cm³
            volume_cm3 = raw_vol / 1_000.0
        else:
            # cm units already
            volume_cm3 = raw_vol

        logger.info("trimesh raw_vol=%.6f max_extent=%.3f → %.2f cm³", raw_vol, max_extent, volume_cm3)

        if volume_cm3 < 0.1 or volume_cm3 > 50_000.0:
            raise ValueError(f"Volume out of printable range: {volume_cm3:.2f} cm³")

        fill  = _INFILL_FACTOR + _WALL_FACTOR
        grams = volume_cm3 * fill * _PLA_DENSITY_G_PER_CM3
        hours = (grams / _PRINT_SPEED_G_PER_MIN) / 60.0

        grams = round(max(5.0, min(300.0, grams)), 1)
        hours = round(max(0.25, min(24.0, hours)), 2)

        logger.info("trimesh slice — vol=%.1f cm³, %.1fg, %.2fh", volume_cm3, grams, hours)
        return SliceResult(grams=grams, print_hours=hours, tmf_path=None, stl_path=stl_path)

    except Exception as exc:
        logger.warning("trimesh failed (%s) — falling back to dimensions", exc)
        fallback = _estimate_from_dimensions(dimensions_hint)
        # Keep the STL we already saved so the viewer still works
        return SliceResult(
            grams=fallback.grams,
            print_hours=fallback.print_hours,
            tmf_path=None,
            stl_path=stl_path,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ── Shared output parser ──────────────────────────────────────────────────────

def _parse_slicer_stdout(stdout: str) -> tuple[float, float]:
    grams = 0.0
    hours = 0.0

    gram_match = re.search(r"Filament used[^=\n]*[=:\s]+([0-9.]+)\s*g", stdout, re.IGNORECASE)
    if gram_match:
        grams = float(gram_match.group(1))

    # BambuStudio outputs something like: "Total filament weight: 12.34g"
    if grams == 0.0:
        alt = re.search(r"(?:total\s+filament|filament\s+weight)[^0-9]*([0-9.]+)\s*g", stdout, re.IGNORECASE)
        if alt:
            grams = float(alt.group(1))

    time_match = re.search(
        r"Print time[:\s]+(?:(\d+)h\s*)?(?:(\d+)m)?", stdout, re.IGNORECASE
    )
    if time_match:
        h = int(time_match.group(1) or 0)
        m = int(time_match.group(2) or 0)
        hours = h + m / 60.0

    return grams, hours


# ── STL persistence for 3D viewer ─────────────────────────────────────────────

_VIEWER_STL = Path(tempfile.gettempdir()) / "print3d_current.stl"


def _persist_stl(src: Path) -> str | None:
    """Copy src to a stable path so the viewer can serve it. Returns path or None."""
    try:
        import trimesh  # type: ignore
        if src.suffix.lower() == ".stl":
            _VIEWER_STL.write_bytes(src.read_bytes())
        else:
            mesh = trimesh.load(str(src), force="mesh")
            mesh.export(str(_VIEWER_STL))
        return str(_VIEWER_STL)
    except Exception as exc:
        logger.warning("Could not persist STL for viewer: %s", exc)
        return None


def get_viewer_stl_path() -> Path:
    return _VIEWER_STL


# ── Dimension fallback (last resort) ─────────────────────────────────────────

def _estimate_from_dimensions(dimensions_hint: str) -> SliceResult:
    numbers = re.findall(r"\d+(?:\.\d+)?", dimensions_hint)

    if len(numbers) >= 3:
        dims = sorted([float(n) for n in numbers[:3]])
        volume_cm3 = dims[0] * dims[1] * dims[2] * 0.4  # 40% fill of bounding box (hollow organic shapes)
    elif len(numbers) == 2:
        a, b = float(numbers[0]), float(numbers[1])
        volume_cm3 = max(a, b) * (min(a, b) ** 2) * 0.08  # thin cylindrical approximation
    elif len(numbers) == 1:
        d = float(numbers[0])
        # Figurine-like: height d, width ~d*0.4, depth ~d*0.3, 50% hollow
        volume_cm3 = d * (d * 0.40) * (d * 0.30) * 0.5
    else:
        return SliceResult(grams=45.0, print_hours=2.5, tmf_path=None, stl_path=None)

    fill  = _INFILL_FACTOR + _WALL_FACTOR
    grams = volume_cm3 * fill * _PLA_DENSITY_G_PER_CM3
    grams = round(max(5.0, min(300.0, grams)), 1)
    hours = round(max(0.25, min(20.0, (grams / _PRINT_SPEED_G_PER_MIN) / 60.0)), 2)

    logger.info("Dimension estimate — %.1fg, %.2fh from dims='%s'", grams, hours, dimensions_hint)
    return SliceResult(grams=grams, print_hours=hours, tmf_path=None, stl_path=None)
