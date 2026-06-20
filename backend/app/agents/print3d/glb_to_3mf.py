"""GLB → Bambu Studio 3MF converter.

Vendored from OssMansour/glb_to_3mf_package (private repo).
Adaptations for our codebase:
  - convert(glb_path, output_path) public API (jobs.py entry point)
  - source_name threaded through build_model_settings / write_bambu_project
  - TEMPLATE_BAMBU_PROJECT defaults to None when BAMBU_TEMPLATE_3MF unset (falls back to {})
  - LOKY_MAX_CPU_COUNT / joblib warning suppression preserved
  - module-level logger for convert() entry/exit; internal print/tqdm unchanged
"""
import base64
import datetime as dt
import json
import logging
import os
import warnings
import zipfile
from html import escape
from pathlib import Path

import numpy as np
import trimesh

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
warnings.filterwarnings(
    "ignore",
    message="Could not find the number of physical cores.*",
    category=UserWarning,
    module="joblib.externals.loky.backend.context",
)

from sklearn.cluster import KMeans
from skimage.color import rgb2lab
from scipy.spatial import cKDTree
import maxflow
from tqdm import tqdm

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INPUT_FILE = os.environ.get("GLB_INPUT_FILE", "input.glb")
OUTPUT_FILE = os.environ.get("THREEMF_OUTPUT_FILE", "output.3mf")
# None when env var is unset — template_project_settings checks `is not None` before .exists()
# (Path("") resolves to Path(".") in pathlib, so .exists() would return True = wrong)
_template_env = os.environ.get("BAMBU_TEMPLATE_3MF", "")
TEMPLATE_BAMBU_PROJECT: Path | None = Path(_template_env) if _template_env else None

NUM_COLORS = 4
BUILD_SCALE = 100.0

# "figurine" snaps near-grayscale extremes of the natural KMeans palette to
# pure black / pure white (slot displayed as #000000 / #FFFFFF). This keeps
# crisp printed details on extremes WITHOUT wasting a slot when the figurine
# does not actually have a near-pure black or white among its top-N colors.
# "general" leaves all centroids as the per-cluster mean RGB.
MODE = "figurine"

# Snap thresholds (CIELAB)
BLACK_SNAP_LSTAR = 25       # centroid L* below this → snap to pure black
WHITE_SNAP_LSTAR = 92       # centroid L* above this → snap to pure white
SNAP_MAX_CHROMA = 18        # only snap if a*²+b*² is small (near-grayscale)

# Shading-invariant color metric.
#
# Under Lambertian shading  observed = albedo × shading : darkening a surface
# lowers L* and proportionally lowers chroma but PRESERVES hue. Clustering and
# distance therefore key on hue (for chromatic colors) and on lightness (for
# achromatic colors), so every shade of one material — highlight to deep
# shadow — collapses to a single filament. Real-world shadows are reproduced
# physically by the print, so discarding them here is correct, not lossy.
#
# This is deliberately NOT figurine-specific: a near-gray model (chroma below
# the gate everywhere) falls back to pure lightness clustering automatically,
# and an object with no near-pure black/white simply never triggers the snap.
#
# Feature vector per color (scaled to be comparable to CIELAB, ~0..140 max):
#     f0 = L* · lightness_weight(conf)
#     f1 = HUE_WEIGHT · conf · cos(hue)
#     f2 = HUE_WEIGHT · conf · sin(hue)
# conf ramps chroma from CHROMA_RAMP_LOW..ACHROMATIC_CHROMA_GATE → [0,1];
# lightness_weight ramps 1 (gray: separate black/gray/white by L*) down to
# HUE_LIGHTNESS_WEIGHT (saturated: merge shades of one hue across lightness).
ACHROMATIC_CHROMA_GATE = 20.0   # chroma at/above which hue is fully trusted
CHROMA_RAMP_LOW = 8.0           # chroma below which a color is treated as gray
HUE_WEIGHT = 50.0               # weight of the hue direction vs lightness
HUE_LIGHTNESS_WEIGHT = 0.25     # residual lightness weight for saturated colors

# Per-face texture sampling.
# 13 = 3 vertices + 3 mid-edges + 1 center + 6 mid-interior, median-voted.
# Median (not mean) ensures a face that is 8/13 red and 5/13 black is
# assigned red, not a muddy dark-red that confuses the clusterer.
COLOR_SAMPLES_PER_FACE = 13

# Mesh repair
# REMESH_MODE controls when voxel remeshing is used:
#   "off"   — never remesh; let Bambu Studio repair minor defects itself.
#             Best for detailed figurines where voxel quantization is visible.
#   "auto"  — remesh only when the mesh has many boundary edges (severely broken).
#             Uses BOUNDARY_EDGE_THRESHOLD to decide.
#   "force" — always remesh when not watertight, regardless of defect severity.
# For most detailed figures, start with "off" and only enable if Bambu
# Studio fails to slice the model.
REMESH_MODE = "auto"   # "off" | "auto" | "force"
VOXEL_PITCH_RATIO = 0.005

# Printer-aware voxel remesh constraints.
# Pitch is clamped to [VOXEL_PITCH_MIN_MM, VOXEL_PITCH_MAX_MM] so it stays
# within meaningful print-resolution bounds regardless of model size.
# MAX_REMESH_FACES guards against marching-cubes producing a slicer-hostile
# face count; BOUNDARY_EDGE_THRESHOLD decides whether a mesh is damaged
# enough to warrant full voxel remesh vs. basic repair only.
NOZZLE_DIAMETER_MM = 0.4
LAYER_HEIGHT_MM = 0.16
VOXEL_PITCH_MIN_MM = 0.10
VOXEL_PITCH_MAX_MM = 0.30
MAX_REMESH_FACES = 600_000
BOUNDARY_EDGE_THRESHOLD = 100   # fewer boundary edges → skip voxel remesh

# Post-voxel-remesh surface smoothing.
# Marching-cubes output has visible staircase artefacts.  Taubin smoothing
# + partial reprojection toward the original mesh reduces these without
# collapsing sharp features or shrinking the model.
# Set REMESH_SMOOTH_ITERS = 0 to disable smoothing entirely.
REMESH_SMOOTH_ITERS    = 8      # Taubin passes before reprojection
REMESH_REPROJECT_STR  = 0.35   # 0 = no reproject, 1 = snap fully to original
REMESH_FINAL_ITERS    = 3      # Taubin passes after reprojection

# Graph-cut label smoothing
SMOOTHNESS_WEIGHT = 40.0
GRAPHCUT_OUTER_ITERATIONS = 4
CREASE_ANGLE_DEG = 20.0

# Region cleanup
SNAPPED_MIN_REGION_FACES = 15   # used for snapped-to-pure (black/white) slots
SALIENT_MIN_REGION_FACES = 8    # used for saliency-promoted (rare-but-important) slots
FREE_MIN_REGION_FACES = 50      # used for natural-centroid slots

# Color-contrast edge weight for graph-cut smoothness.
# Adjacent face pairs whose sampled colors differ by more than this ΔE
# (CIELAB) get a proportionally lower smoothness penalty, so the graph cut
# is free to place label boundaries where the texture already shows an edge.
# Good range: 10–20. Lower = more detail-preserving, higher = smoother.
COLOR_CONTRAST_SIGMA = 15.0

# Final color-boundary cleaning (color-free MRF/Potts label denoising).
#
# Runs on the OUTPUT mesh, AFTER any voxel remesh. The graph-cut smoothing
# above runs on the pre-remesh mesh; voxel-remesh label transfer then
# re-introduces speckle and ragged fringe at every color border, and nothing
# smooths it afterward. This stage closes that gap: it minimizes a Potts
# energy on the final face graph (boundary length weighted by shared-edge
# length and creases) to straighten zig-zag borders and remove speckle.
# It needs only the label field, not colors, so it works post-remesh.
#
# STAY_COST anchors each face to its current label and is set ABOVE
# SMOOTHNESS so thin coherent lines (logo strokes, outlines) are preserved —
# only locally-inconsistent speckle flips. Salient slots are also protected.
# Set BOUNDARY_CLEAN_ENABLE = False to skip this stage entirely.
BOUNDARY_CLEAN_ENABLE = True
BOUNDARY_CLEAN_SMOOTHNESS = 6.0        # Potts weight; higher = cleaner/straighter, riskier to thin features
BOUNDARY_CLEAN_STAY_COST = 9.0         # anchor to current label; keep > SMOOTHNESS to protect thin lines
BOUNDARY_CLEAN_ITERS = 3               # α-expansion sweeps
BOUNDARY_CLEAN_CREASE_ANGLE_DEG = 25.0 # boundaries may still follow edges sharper than this
BOUNDARY_CLEAN_DESPECKLE_FACES = 24    # after regularization, drop non-salient regions smaller than this

# Saliency-aware palette selection (over-cluster + score + select).
#
# Replaces direct KMeans-to-N with a two-stage pipeline:
#   1. Cluster face colors into CANDIDATE_COLORS centroids in the
#      shading-invariant feature space (shades of one hue collapse together).
#   2. Score each candidate on (area, boundary contrast, compactness,
#      reconstruction error if removed) and greedily pick the top
#      NUM_COLORS with a maximin-LAB-distance diversity bonus.
#
# This lets a small but high-contrast / high-recon-error cluster (e.g.
# white eye lenses on Spider-Man) win a slot over a 4th near-duplicate of
# the dominant color, which pure top-N-by-area KMeans cannot do.
#
# Background: over-cluster + rerank is standard in superpixel segmentation
# (SLIC, Achanta et al. 2012); reconstruction-error importance follows the
# Information Bottleneck framing (Tishby 1999); maximin-diversity greedy
# is (1-1/e)-approximate for submodular subset selection (Krause &
# Golovin 2014); ΔE in CIELAB is the ISO standard perceptual distance.
CANDIDATE_COLORS = 16

SCORE_AREA_WEIGHT = 0.40
SCORE_CONTRAST_WEIGHT = 0.30
SCORE_COMPACTNESS_WEIGHT = 0.15
SCORE_RECON_WEIGHT = 0.15

SELECTION_DIVERSITY_LAMBDA = 0.20

# A selected candidate is flagged "salient" when its area is below
# SALIENT_AREA_MAX but its non-area scores average above SALIENT_OTHER_MIN.
# Salient labels get the smaller region-cleanup threshold.
SALIENT_AREA_MAX = 0.05
SALIENT_OTHER_MIN = 0.50

BAMBU_PAINT_CODES = ["4", "8", "0C", "1C", "2C", "3C", "4C", "5C"]
TRANSPARENT_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADElEQVR42mP8z8BQDwAF"
    "gwJ/lv0Z2wAAAABJRU5ErkJggg=="
)


# ---------------------------------------------------------------------------
# Mesh loading and per-face color sampling
# ---------------------------------------------------------------------------

def load_mesh(path):
    scene = trimesh.load(path)
    if isinstance(scene, trimesh.Scene):
        mesh = trimesh.util.concatenate(scene.dump())
    else:
        mesh = scene
    return mesh


def sample_face_colors(mesh, samples_per_face=None):
    """Return one RGB color per face, sampled with multi-point averaging.

    Strategy:
      1. If the mesh has a real texture + UVs, sample N texels per face
         (vertices + mid-edges + center) and take the mean. This captures
         the dominant color of the face on high-frequency textures.
      2. Otherwise fall back to vertex_colors barycenter, then to
         baseColorFactor, then to neutral gray.

    Texture path is tried FIRST because trimesh's TextureVisuals exposes a
    synthetic vertex_colors property that is sampled per-vertex (per UV) and
    then linearly interpolated — for triangle-soup textured GLBs this can be
    less accurate than sampling the texture directly at face barycenters.

    Must be called BEFORE any mesh repair so the original UV / vertex_color
    mapping is intact.
    """
    if samples_per_face is None:
        samples_per_face = COLOR_SAMPLES_PER_FACE

    n_faces = len(mesh.faces)

    material = getattr(mesh.visual, "material", None)
    texture = None
    if material is not None:
        texture = getattr(material, "image", None)
        if texture is None:
            texture = getattr(material, "baseColorTexture", None)
    uv = getattr(mesh.visual, "uv", None)

    if uv is not None and texture is not None:
        return _sample_texture_at_face_points(
            mesh, np.asarray(uv), np.asarray(texture), samples_per_face
        )

    vc_attr = getattr(mesh.visual, "vertex_colors", None)
    if vc_attr is not None and len(vc_attr) > 0:
        vc = np.asarray(vc_attr)[:, :3].astype(np.float64)
        return vc[mesh.faces].mean(axis=1).astype(np.uint8)

    base_color = getattr(material, "baseColorFactor", None) if material else None
    if base_color is not None:
        bc = np.array(base_color[:3], dtype=float)
        if bc.max() <= 1.0:
            bc *= 255
        return np.tile(bc.astype(np.uint8), (n_faces, 1))

    return np.full((n_faces, 3), 128, dtype=np.uint8)


def _sample_texture_at_face_points(mesh, uv, image, samples_per_face):
    if image.ndim == 2:
        image = np.stack([image, image, image], axis=-1)
    if image.shape[2] >= 4:
        image = image[..., :3]
    h, w = image.shape[:2]

    v0 = uv[mesh.faces[:, 0]]
    v1 = uv[mesh.faces[:, 1]]
    v2 = uv[mesh.faces[:, 2]]
    centroid = (v0 + v1 + v2) / 3
    m01 = (v0 + v1) / 2
    m12 = (v1 + v2) / 2
    m02 = (v0 + v2) / 2

    # Always include the 3 vertices.
    sample_uvs = [v0, v1, v2]
    if samples_per_face >= 4:
        # + barycentric centroid
        sample_uvs.append(centroid)
    if samples_per_face >= 7:
        # + 3 edge midpoints
        sample_uvs.append(m01)
        sample_uvs.append(m12)
        sample_uvs.append(m02)
    if samples_per_face >= 13:
        # + 6 mid-interior points (midpoints between centroid and
        # each vertex / edge-midpoint). These fill the triangle interior
        # more uniformly, giving the per-channel median a clear majority
        # even on faces that straddle two color regions.
        sample_uvs.append((v0 + centroid) / 2)
        sample_uvs.append((v1 + centroid) / 2)
        sample_uvs.append((v2 + centroid) / 2)
        sample_uvs.append((m01 + centroid) / 2)
        sample_uvs.append((m12 + centroid) / 2)
        sample_uvs.append((m02 + centroid) / 2)
    sample_uvs = np.stack(sample_uvs, axis=1)  # (n_faces, S, 2)

    px = np.clip((sample_uvs[..., 0] * (w - 1)).astype(int), 0, w - 1)
    py = np.clip(((1 - sample_uvs[..., 1]) * (h - 1)).astype(int), 0, h - 1)

    sampled = image[py, px].astype(np.float64)  # (n_faces, S, 3)
    # Median per channel: a face that is 8/13 red and 5/13 black stays red,
    # rather than blending to a dark-red that confuses the clusterer.
    return np.median(sampled, axis=1).astype(np.uint8)


# ---------------------------------------------------------------------------
# Mesh repair: basic repair (always) + voxel-remesh-with-label-transfer (fallback)
# ---------------------------------------------------------------------------

def basic_repair_mesh(mesh, face_colors):
    """Weld + dedup + hole-fill + normal-fix. No voxel remesh.

    Per-face color is preserved exactly: welding does not change face order;
    dedup and degenerate removal use boolean masks; fill_holes appends new
    faces with color copied from the nearest existing face by centroid.

    Returns (mesh, face_colors).
    """
    print(
        f"  before repair: verts={len(mesh.vertices)} "
        f"faces={len(mesh.faces)} watertight={mesh.is_watertight}"
    )

    try:
        mesh.merge_vertices(merge_tex=True, merge_norm=True)
    except TypeError:
        mesh.merge_vertices()

    unique_mask = mesh.unique_faces()
    if not unique_mask.all():
        mesh.update_faces(unique_mask)
        face_colors = face_colors[unique_mask]

    nondeg_mask = mesh.nondegenerate_faces()
    if not nondeg_mask.all():
        mesh.update_faces(nondeg_mask)
        face_colors = face_colors[nondeg_mask]

    mesh.remove_unreferenced_vertices()

    n_before = len(mesh.faces)
    try:
        mesh.fill_holes()
    except Exception as e:
        print(f"  fill_holes failed: {e}")
    n_after = len(mesh.faces)
    if n_after > n_before:
        existing_centers = mesh.triangles[:n_before].mean(axis=1)
        new_centers = mesh.triangles[n_before:].mean(axis=1)
        tree = cKDTree(existing_centers)
        _, nearest = tree.query(new_centers, k=1)
        face_colors = np.vstack([face_colors, face_colors[nearest]])

    try:
        mesh.fix_normals()
    except Exception as e:
        print(f"  fix_normals failed: {e}")

    print(
        f"  after basic repair: verts={len(mesh.vertices)} "
        f"faces={len(mesh.faces)} watertight={mesh.is_watertight}"
    )

    return mesh, face_colors


def compute_print_aware_voxel_pitch(mesh):
    """Return a voxel pitch that balances printer resolution and face-count budget.

    Two constraints are reconciled:

    1. Printer resolution: pitch is derived from min(nozzle/2, layer_height)
       converted to model-space units (1 model unit = BUILD_SCALE mm), then
       clamped to [VOXEL_PITCH_MIN_MM, VOXEL_PITCH_MAX_MM].

    2. Face-count budget: marching-cubes surface faces ≈ 2·area/pitch², so
       the minimum pitch that keeps faces under MAX_REMESH_FACES is
       √(2·area / MAX_REMESH_FACES). If this is coarser than the
       printer-resolution pitch, the budget floor wins — we accept a
       slightly coarser remesh rather than blowing past the face limit.
    """
    model_unit = 1.0 / BUILD_SCALE          # 1 mm expressed in model units
    pitch_min = VOXEL_PITCH_MIN_MM * model_unit
    pitch_max = VOXEL_PITCH_MAX_MM * model_unit
    machine = min(NOZZLE_DIAMETER_MM * 0.5, LAYER_HEIGHT_MM) * model_unit
    relative = float(mesh.extents.max() * VOXEL_PITCH_RATIO)
    pitch = float(np.clip(min(relative, machine), pitch_min, pitch_max))

    # Face-count floor: if the surface area demands a coarser pitch to stay
    # under MAX_REMESH_FACES, raise pitch accordingly (may exceed pitch_max).
    # Factor 6.0 is conservative: marching-cubes produces ~4-6× area/pitch²
    # faces in practice (worse than the 2× isotropic-surface approximation).
    area = float(mesh.area)
    if area > 0 and MAX_REMESH_FACES > 0:
        pitch_budget = float(np.sqrt(6.0 * area / MAX_REMESH_FACES))
        if pitch_budget > pitch:
            pitch = max(pitch_budget, pitch_min)
            print(
                f"  face-count budget raised pitch to {pitch:.6f} model units "
                f"({pitch * BUILD_SCALE:.4f} mm) to stay under "
                f"{MAX_REMESH_FACES:,} faces"
            )

    return pitch


def should_voxel_remesh(mesh):
    """Return True only when the mesh is damaged enough to warrant remesh.

    REMESH_MODE == "off"   → always False (caller should not even call this)
    REMESH_MODE == "force" → always True when mesh is not watertight
    REMESH_MODE == "auto"  → True only when boundary-edge count is high,
                             indicating genuinely broken geometry rather than
                             minor open edges that the slicer can handle.
    """
    if mesh.is_watertight:
        return False
    if REMESH_MODE == "off":
        return False
    if REMESH_MODE == "force":
        return True
    # auto: check boundary edge count
    try:
        n_boundary = len(mesh.edges_boundary)
    except Exception:
        n_boundary = BOUNDARY_EDGE_THRESHOLD + 1
    if n_boundary < BOUNDARY_EDGE_THRESHOLD:
        print(
            f"  mesh has only {n_boundary} boundary edges — "
            "skipping voxel remesh (defects too minor)"
        )
        return False
    return True


def _triangle_sample_points(triangles):
    """Return (n_faces, 7, 3) array of sample points per triangle.

    Samples: centroid + 3 vertices + 3 edge midpoints.
    """
    v0 = triangles[:, 0]
    v1 = triangles[:, 1]
    v2 = triangles[:, 2]
    centroid = (v0 + v1 + v2) / 3
    return np.stack(
        [centroid, v0, v1, v2,
         (v0 + v1) / 2, (v1 + v2) / 2, (v0 + v2) / 2],
        axis=1,
    )  # (n_faces, 7, 3)


def _transfer_labels_majority(old_mesh, old_labels, new_mesh,
                              salient_labels=None, batch=50_000):
    """Transfer labels from old_mesh to new_mesh via 7-point majority vote.

    For each new triangle, 7 3-D sample points (centroid, vertices,
    edge midpoints) are projected onto the old mesh surface.  Each receives
    the label of its closest old triangle.  The new triangle gets the
    majority-vote label among those 7.

    If salient_labels is provided, any salient label that appears in at
    least 2 of the 7 samples wins outright — this preserves small important
    features (eye lenses, logos) that would otherwise lose to majority noise.
    """
    n_labels = int(old_labels.max()) + 1
    samples = _triangle_sample_points(new_mesh.triangles)  # (F, 7, 3)
    n_faces, n_samples, _ = samples.shape
    flat = samples.reshape(-1, 3)                          # (F*7, 3)

    hit_labels = np.empty(len(flat), dtype=np.int64)
    for start in tqdm(
        range(0, len(flat), batch),
        desc="  label transfer",
        unit="batch",
        leave=False,
    ):
        end = min(start + batch, len(flat))
        _, _, fids = trimesh.proximity.closest_point(old_mesh, flat[start:end])
        fids = np.clip(np.asarray(fids, dtype=np.int64), 0, len(old_labels) - 1)
        hit_labels[start:end] = old_labels[fids]

    vote_matrix = hit_labels.reshape(n_faces, n_samples)   # (F, 7)

    new_labels = np.empty(n_faces, dtype=np.uint32)
    for i in range(n_faces):
        row = vote_matrix[i]
        if salient_labels:
            for sl in salient_labels:
                if np.sum(row == sl) >= 2:
                    new_labels[i] = sl
                    break
            else:
                new_labels[i] = np.bincount(row, minlength=n_labels).argmax()
        else:
            new_labels[i] = np.bincount(row, minlength=n_labels).argmax()

    return new_labels


import trimesh.smoothing


def smooth_and_reproject_remesh(new_mesh, old_mesh,
                                smooth_iters=None,
                                project_strength=None,
                                final_smooth_iters=None):
    """Reduce voxel stair-stepping while keeping watertight voxel topology.

    Pipeline:
      1. Taubin smoothing (alternating +/- passes) to reduce quantization
         ridges without the shrinkage of plain Laplacian smoothing.
      2. Partial reprojection: each vertex moves partway toward the closest
         point on the original mesh, recovering the original surface shape
         without reintroducing topological defects.
      3. A final light Taubin pass to remove reprojection noise.
      4. Degenerate-face / normal cleanup.

    Vertex movement does not change topology, so watertightness is preserved.
    """
    if smooth_iters is None:
        smooth_iters = REMESH_SMOOTH_ITERS
    if project_strength is None:
        project_strength = REMESH_REPROJECT_STR
    if final_smooth_iters is None:
        final_smooth_iters = REMESH_FINAL_ITERS

    if smooth_iters > 0:
        try:
            trimesh.smoothing.filter_taubin(
                new_mesh, lamb=0.5, nu=-0.53, iterations=smooth_iters
            )
        except Exception as e:
            print(f"  WARNING: Taubin smoothing failed: {e}")

    if project_strength > 0:
        verts = new_mesh.vertices.copy()
        batch = 100_000
        for start in tqdm(
            range(0, len(verts), batch),
            desc="  reproject vertices",
            unit="batch",
            leave=False,
        ):
            end = min(start + batch, len(verts))
            closest, _, _ = trimesh.proximity.closest_point(old_mesh, verts[start:end])
            verts[start:end] = (
                (1.0 - project_strength) * verts[start:end]
                + project_strength * closest
            )
        new_mesh.vertices = verts

    if final_smooth_iters > 0:
        try:
            trimesh.smoothing.filter_taubin(
                new_mesh, lamb=0.3, nu=-0.34, iterations=final_smooth_iters
            )
        except Exception as e:
            print(f"  WARNING: final Taubin smoothing failed: {e}")

    try:
        nondeg = new_mesh.nondegenerate_faces()
        if not nondeg.all():
            new_mesh.update_faces(nondeg)
        new_mesh.remove_unreferenced_vertices()
        new_mesh.fix_normals()
    except Exception as e:
        print(f"  WARNING: post-smooth cleanup failed: {e}")

    return new_mesh


def voxel_remesh_with_label_transfer(mesh, labels,
                                     salient_labels=None,
                                     voxel_pitch_ratio=VOXEL_PITCH_RATIO):
    """Printer-aware voxel remesh with validated label transfer.

    Steps:
      1. Compute a print-aware pitch (clamped to nozzle/layer resolution).
      2. Voxelize, fill, and extract marching-cubes surface.
      3. Validate face count and bounding-box change.
      4. Transfer labels via 7-point majority vote; honour salient labels.
    """
    pitch = compute_print_aware_voxel_pitch(mesh)
    pitch_mm = pitch * BUILD_SCALE
    print(f"  print-aware voxel pitch: {pitch:.6f} model units ({pitch_mm:.4f} mm)")
    old_extents = mesh.extents.copy()

    def _do_remesh(p):
        """Voxelize at pitch p, apply transform, smooth, then return (voxel, new_mesh)."""
        v = mesh.voxelized(p).fill()
        m = v.marching_cubes
        # Bring marching-cubes output into model-space coordinates.
        try:
            m.apply_transform(v.transform)
        except Exception as e:
            print(f"  WARNING: could not apply voxel transform: {e}")
        # Smooth out voxel staircase artefacts and reproject toward original shape.
        if REMESH_SMOOTH_ITERS > 0 or REMESH_REPROJECT_STR > 0:
            m = smooth_and_reproject_remesh(m, mesh)
        return v, m

    with tqdm(total=2, desc="  voxel remesh", unit="step", leave=False) as pbar:
        pbar.set_postfix_str("voxelizing + fill")
        voxel, new_mesh = _do_remesh(pitch)
        pbar.update(1)
        pbar.set_postfix_str("marching cubes")
        pbar.update(1)

    # Retry with coarser pitch if face count exceeds budget.
    retry = 0
    while len(new_mesh.faces) > MAX_REMESH_FACES and retry < 6:
        retry += 1
        pitch *= 1.25
        print(
            f"  face count {len(new_mesh.faces):,} > {MAX_REMESH_FACES:,}; "
            f"retrying with pitch {pitch:.6f} (×1.25, attempt {retry})"
        )
        with tqdm(total=2, desc="  voxel remesh retry", unit="step", leave=False) as pbar:
            pbar.set_postfix_str("voxelizing + fill")
            voxel, new_mesh = _do_remesh(pitch)
            pbar.update(1)
            pbar.set_postfix_str("marching cubes")
            pbar.update(1)
    if len(new_mesh.faces) > MAX_REMESH_FACES:
        print(
            f"  WARNING: remesh still {len(new_mesh.faces):,} faces after {retry} retries; "
            "continuing anyway"
        )

    # Validate bounding-box change on significant dimensions only.
    # Thin open meshes legitimately gain thickness after voxelization;
    # ignore dimensions < 1% of the largest original extent.
    new_extents = new_mesh.extents
    significant = old_extents > (old_extents.max() * 0.01)
    if significant.any():
        rel = np.abs(new_extents - old_extents) / np.maximum(old_extents, 1e-9)
        extent_change = float(rel[significant].max())
    else:
        extent_change = 0.0
    if extent_change > 0.10:
        raise RuntimeError(
            f"Voxel remesh invalid: bounding box changed by {extent_change:.1%} on "
            "significant dimensions after applying voxel.transform. "
            "Label transfer and 3MF output would be corrupted. "
            "Set ALLOW_VOXEL_REMESH = False to skip remesh."
        )

    # Multi-sample majority-vote label transfer.
    new_labels = _transfer_labels_majority(
        old_mesh=mesh,
        old_labels=labels,
        new_mesh=new_mesh,
        salient_labels=salient_labels,
    )

    print(
        f"  after voxel remesh: verts={len(new_mesh.vertices)} "
        f"faces={len(new_mesh.faces)} watertight={new_mesh.is_watertight}"
    )
    return new_mesh, new_labels.astype(np.uint32)


# ---------------------------------------------------------------------------
# Color clustering (in CIELAB) + snap-to-pure for extreme centroids
# ---------------------------------------------------------------------------

def rgb_to_lab(rgb_uint8):
    rgb = np.asarray(rgb_uint8, dtype=np.float64) / 255.0
    if rgb.ndim == 1:
        return rgb2lab(rgb[None, None, :])[0, 0]
    return rgb2lab(rgb[None, :, :])[0]


def shading_invariant_features(rgb_uint8):
    """Map RGB → shading-invariant feature space (see config block for theory).

    Returns an (N, 3) float array (or (3,) for a single color). Distances in
    this space treat shades of one hue as one color while keeping black, gray
    and white separated by lightness. Scale is comparable to CIELAB so the
    existing SMOOTHNESS_WEIGHT / COLOR_CONTRAST_SIGMA stay meaningful.
    """
    arr = np.asarray(rgb_uint8, dtype=np.float64)
    single = arr.ndim == 1
    if single:
        arr = arr[None, :]

    lab = rgb_to_lab(arr)
    L = lab[:, 0]
    a = lab[:, 1]
    b = lab[:, 2]
    chroma = np.sqrt(a * a + b * b)
    hue = np.arctan2(b, a)

    denom = max(ACHROMATIC_CHROMA_GATE - CHROMA_RAMP_LOW, 1e-6)
    conf = np.clip((chroma - CHROMA_RAMP_LOW) / denom, 0.0, 1.0)
    lightness_weight = 1.0 - conf * (1.0 - HUE_LIGHTNESS_WEIGHT)

    f0 = L * lightness_weight
    f1 = HUE_WEIGHT * conf * np.cos(hue)
    f2 = HUE_WEIGHT * conf * np.sin(hue)
    feat = np.stack([f0, f1, f2], axis=1)
    return feat[0] if single else feat


def _cluster_colors(face_colors_rgb, n_clusters):
    """Weighted KMeans in shading-invariant feature space.

    Clusters by hue (chromatic) / lightness (achromatic) so shades of one
    material group together. The returned palette is still the mean *RGB* of
    each cluster (a human-/printer-meaningful color), sorted dark→light.
    Returns (palette_rgb, labels).
    """
    n = len(face_colors_rgb)
    if n == 0 or n_clusters <= 0:
        return (
            np.empty((0, 3), dtype=np.uint8),
            np.zeros(n, dtype=np.uint32),
        )

    unique_rgb, inverse, counts = np.unique(
        np.asarray(face_colors_rgb), axis=0, return_inverse=True, return_counts=True
    )
    n_clusters = min(n_clusters, len(unique_rgb))
    if n_clusters == 0:
        return (
            np.empty((0, 3), dtype=np.uint8),
            np.zeros(n, dtype=np.uint32),
        )

    unique_feat = shading_invariant_features(unique_rgb)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    kmeans.fit(unique_feat, sample_weight=counts)
    labels_unique = kmeans.predict(unique_feat)
    labels = labels_unique[inverse].astype(np.uint32)

    palette = np.zeros((n_clusters, 3), dtype=np.uint8)
    for c in range(n_clusters):
        mask = labels == c
        if mask.any():
            palette[c] = np.mean(face_colors_rgb[mask], axis=0).astype(np.uint8)

    luminance = palette @ np.array([0.2126, 0.7152, 0.0722])
    order = np.argsort(luminance)
    palette = palette[order]
    remap = np.zeros(n_clusters, dtype=np.uint32)
    remap[order] = np.arange(n_clusters)
    labels = remap[labels]
    return palette, labels


def snap_extreme_to_pure(palette_rgb):
    """Snap centroids near extreme luminance + low chroma to pure black/white.

    Returns (snapped_palette, set_of_snapped_indices).

    Only snaps when BOTH luminance is extreme AND chroma is low — so a deep
    navy (L*≈20, chroma≈30) stays as navy, not black.
    """
    if len(palette_rgb) == 0:
        return palette_rgb.copy(), set()

    palette_lab = rgb_to_lab(palette_rgb)
    L = palette_lab[:, 0]
    a = palette_lab[:, 1]
    b = palette_lab[:, 2]
    chroma = np.sqrt(a * a + b * b)

    snapped = palette_rgb.copy()
    snapped_set = set()
    for i in range(len(palette_rgb)):
        if L[i] <= BLACK_SNAP_LSTAR and chroma[i] <= SNAP_MAX_CHROMA:
            snapped[i] = [0, 0, 0]
            snapped_set.add(i)
        elif L[i] >= WHITE_SNAP_LSTAR and chroma[i] <= SNAP_MAX_CHROMA:
            snapped[i] = [255, 255, 255]
            snapped_set.add(i)
    return snapped, snapped_set


# ---------------------------------------------------------------------------
# Saliency-aware candidate scoring and palette selection
# ---------------------------------------------------------------------------

def score_candidate_colors(mesh, face_colors_rgb,
                           candidate_palette, candidate_labels):
    """Multi-criterion importance scoring for over-clustered candidates.

    For each candidate cluster, compute (each normalized to [0, 1]):

      area        : sqrt(face fraction). Sqrt-compressing the ratio prevents
                    a 50%-area cluster from drowning a 1% one on this axis.
      contrast    : mean CIELAB ΔE across edges where one face is in this
                    cluster and the neighbor is not. Identity-critical
                    features (eye whites, outline blacks) sit on
                    high-contrast borders.
      compactness : faces in the largest connected component / total
                    cluster faces. High = coherent; low = scatter noise.
      reconstruction : per-face mean LAB error increase if this cluster's
                    faces are reassigned to the nearest other candidate.
                    Captures "removing this color leaves no good
                    substitute".

    Returns dict with per-candidate arrays (each (n_candidates,)) plus a
    weighted `total`.
    """
    n_faces = len(candidate_labels)
    n_candidates = len(candidate_palette)
    candidate_lab = rgb_to_lab(candidate_palette)
    face_lab = rgb_to_lab(face_colors_rgb)
    candidate_feat = shading_invariant_features(candidate_palette)
    face_feat = shading_invariant_features(face_colors_rgb)
    adjacency = np.asarray(mesh.face_adjacency)

    counts = np.bincount(candidate_labels, minlength=n_candidates).astype(np.float64)

    # --- Area (sqrt-compressed, normalized) ---
    # area_ratio is the true face fraction; used by identify_salient_labels.
    # area is sqrt-compressed for scoring so large clusters don't dominate.
    area_ratio = counts / max(n_faces, 1)
    area_raw = np.sqrt(area_ratio)
    area = area_raw / max(area_raw.max(), 1e-9)

    # --- Boundary contrast ---
    contrast_sum = np.zeros(n_candidates)
    contrast_n = np.zeros(n_candidates)
    if len(adjacency) > 0:
        ea = adjacency[:, 0]
        eb = adjacency[:, 1]
        la = candidate_labels[ea]
        lb = candidate_labels[eb]
        diff = la != lb
        if diff.any():
            d = np.linalg.norm(face_lab[ea[diff]] - face_lab[eb[diff]], axis=1)
            np.add.at(contrast_sum, la[diff], d)
            np.add.at(contrast_n, la[diff], 1)
            np.add.at(contrast_sum, lb[diff], d)
            np.add.at(contrast_n, lb[diff], 1)
    contrast_raw = contrast_sum / np.maximum(contrast_n, 1)
    contrast = contrast_raw / max(contrast_raw.max(), 1e-9)

    # --- Compactness (largest connected component / total per cluster) ---
    compactness = np.zeros(n_candidates)
    if len(adjacency) > 0:
        same = candidate_labels[adjacency[:, 0]] == candidate_labels[adjacency[:, 1]]
        same_adj = adjacency[same]
        neighbors = [[] for _ in range(n_faces)]
        for a, b in same_adj:
            neighbors[int(a)].append(int(b))
            neighbors[int(b)].append(int(a))

        largest = np.zeros(n_candidates)
        visited = np.zeros(n_faces, dtype=bool)
        for start in range(n_faces):
            if visited[start]:
                continue
            label = int(candidate_labels[start])
            stack = [start]
            size = 0
            visited[start] = True
            while stack:
                f = stack.pop()
                size += 1
                for nb in neighbors[f]:
                    if not visited[nb]:
                        visited[nb] = True
                        stack.append(nb)
            if size > largest[label]:
                largest[label] = size
        compactness = largest / np.maximum(counts, 1)

    # --- Reconstruction error if cluster is removed ---
    # Measured in shading-invariant space: a candidate that is just a shade of
    # another (e.g. a red shadow vs red) has a near-zero removal cost and is
    # correctly NOT treated as important, while a genuinely distinct color
    # (white eyes vs everything else) has a high removal cost.
    recon_raw = np.zeros(n_candidates)
    if n_candidates > 1:
        for c in range(n_candidates):
            mask = candidate_labels == c
            if not mask.any():
                continue
            cluster_feat = face_feat[mask]
            original_dist = np.linalg.norm(cluster_feat - candidate_feat[c], axis=1)
            other_feat = np.delete(candidate_feat, c, axis=0)
            dist_others = np.linalg.norm(
                cluster_feat[:, None, :] - other_feat[None, :, :], axis=2
            )
            new_dist = dist_others.min(axis=1)
            recon_raw[c] = float(np.maximum(new_dist - original_dist, 0).mean())
    recon = recon_raw / max(recon_raw.max(), 1e-9)

    total = (
        SCORE_AREA_WEIGHT * area
        + SCORE_CONTRAST_WEIGHT * contrast
        + SCORE_COMPACTNESS_WEIGHT * compactness
        + SCORE_RECON_WEIGHT * recon
    )

    return {
        "counts": counts,
        "area_ratio": area_ratio,
        "area": area,
        "contrast": contrast,
        "contrast_raw": contrast_raw,
        "compactness": compactness,
        "reconstruction": recon,
        "reconstruction_raw": recon_raw,
        "total": total,
    }


def select_top_n_with_diversity(scores, candidate_palette, n_select,
                                diversity_lambda=None):
    """Greedy maximin-diversity subset selection over candidates.

    On each step the next pick maximizes::

        total_score[c] + diversity_lambda * min_{s in selected} Δ(c, s) / max_d

    where Δ is distance in the shading-invariant space, so the maximin term
    spreads picks across HUES (and black/gray/white levels) rather than across
    lightness. This stops the selector from spending two slots on a light and
    a dark shade of the same material.
    """
    if diversity_lambda is None:
        diversity_lambda = SELECTION_DIVERSITY_LAMBDA

    candidate_feat = shading_invariant_features(candidate_palette)
    n_candidates = len(candidate_palette)
    total = scores["total"].astype(np.float64).copy()
    n_select = min(n_select, n_candidates)

    selected = []
    for _ in range(n_select):
        if not selected:
            best = int(np.argmax(total))
        else:
            sel_feat = candidate_feat[selected]
            d = np.linalg.norm(
                candidate_feat[:, None, :] - sel_feat[None, :, :], axis=2
            ).min(axis=1)
            d_norm = d / max(d.max(), 1e-9)
            adjusted = total + diversity_lambda * d_norm
            for s in selected:
                adjusted[s] = -np.inf
            best = int(np.argmax(adjusted))
        selected.append(best)

    return np.array(selected, dtype=np.int64)


def identify_salient_labels(scores, candidate_idx_per_final_label):
    """Final labels whose source candidate was rare-but-important.

    A label is salient if its candidate's TRUE area fraction (not the
    sqrt-compressed scoring value) is below SALIENT_AREA_MAX AND a high
    mean of (contrast, compactness, reconstruction). These get the smaller
    region-cleanup threshold so fine features that earned the slot are
    not erased by graph-cut or region cleanup.
    """
    salient = set()
    for final_label, candidate_idx in enumerate(candidate_idx_per_final_label):
        candidate_idx = int(candidate_idx)
        # Use true area fraction so SALIENT_AREA_MAX = 0.05 means < 5% of faces.
        area = float(scores["area_ratio"][candidate_idx])
        non_area = float(np.mean([
            scores["contrast"][candidate_idx],
            scores["compactness"][candidate_idx],
            scores["reconstruction"][candidate_idx],
        ]))
        if area < SALIENT_AREA_MAX and non_area >= SALIENT_OTHER_MIN:
            salient.add(int(final_label))
    return salient


def print_candidate_score_table(candidate_palette, scores, selected_idx=None):
    print("\n--- Candidate scores (over-clustered, sorted by total) ---")
    header = (
        f"  {'idx':>4} {'hex':>9} {'count':>8} "
        f"{'area':>5} {'cont':>5} {'comp':>5} {'recon':>5} "
        f"{'total':>6}  {'sel':>3}"
    )
    print(header)
    selected_set = set(int(s) for s in (selected_idx if selected_idx is not None else []))
    order = np.argsort(-scores["total"])
    for c in order:
        c = int(c)
        sel_mark = "*" if c in selected_set else ""
        print(
            f"  {c:>4} {color_hex(candidate_palette[c]):>9} "
            f"{int(scores['counts'][c]):>8} "
            f"{scores['area'][c]:>5.2f} {scores['contrast'][c]:>5.2f} "
            f"{scores['compactness'][c]:>5.2f} {scores['reconstruction'][c]:>5.2f} "
            f"{scores['total'][c]:>6.3f}  {sel_mark:>3}"
        )


def choose_face_colors(mesh, face_colors_rgb):
    """Top-N palette via over-cluster + saliency scoring + diverse selection.

    1. Over-cluster face colors in CIELAB to CANDIDATE_COLORS centroids.
    2. Score each candidate on area / contrast / compactness / recon.
    3. Greedy maximin-diversity selection of NUM_COLORS candidates.
    4. Reassign every face to the nearest selected centroid (LAB).
    5. Sort palette by luminance (consistent slot order).
    6. Graph-cut refinement on the face graph.
    7. Region cleanup with smaller threshold for slots whose source
       candidate was salient (rare but high contrast/compactness/recon).
    8. (figurine mode) Snap displayed palette colors near the extremes
       of luminance + low chroma to pure black / pure white. Snap is
       cosmetic — it does not affect cluster math, smoothing, or cleanup.
    9. Compact palette to drop any unused slots.
    """
    n_faces = len(mesh.faces)
    final_colors = min(NUM_COLORS, len(BAMBU_PAINT_CODES))
    candidate_count = max(CANDIDATE_COLORS, final_colors * 2)

    # 1. Over-cluster (in shading-invariant space).
    candidate_palette, candidate_labels = _cluster_colors(
        face_colors_rgb, candidate_count
    )
    if len(candidate_palette) == 0:
        return (
            np.array([[128, 128, 128]], dtype=np.uint8),
            np.zeros(n_faces, dtype=np.uint32),
        )
    candidate_labels = np.asarray(candidate_labels, dtype=np.int64)

    # 2. Score candidates.
    scores = score_candidate_colors(
        mesh, face_colors_rgb, candidate_palette, candidate_labels
    )

    # 3. Greedy diverse selection.
    selected_candidate_idx = select_top_n_with_diversity(
        scores, candidate_palette, final_colors
    )
    print_candidate_score_table(
        candidate_palette, scores, selected_idx=selected_candidate_idx
    )

    # 4. Reassign faces to nearest selected centroid in shading-invariant
    # space. This is the key fix for "shadow eats a slot": a deep-red shadow
    # is nearest to the red centroid by hue, not nearest to black by lightness.
    selected_palette = candidate_palette[selected_candidate_idx]
    face_feat = shading_invariant_features(face_colors_rgb)
    selected_feat = shading_invariant_features(selected_palette)
    distances = np.linalg.norm(
        face_feat[:, None, :] - selected_feat[None, :, :], axis=2
    )
    labels = distances.argmin(axis=1).astype(np.uint32)

    # 5. Sort palette by luminance and remap labels accordingly.
    luminance = selected_palette @ np.array([0.2126, 0.7152, 0.0722])
    order = np.argsort(luminance)
    selected_palette = selected_palette[order]
    selected_feat = shading_invariant_features(selected_palette)
    remap = np.zeros(len(selected_palette), dtype=np.uint32)
    remap[order] = np.arange(len(selected_palette))
    labels = remap[labels]

    # selected_candidate_idx[order[k]] == candidate-id of final-label-k
    candidate_idx_per_final_label = selected_candidate_idx[order]

    # 6. Identify salient labels BEFORE graph cut so we can protect them.
    # Protecting salient faces prevents the graph cut from erasing the rare
    # high-contrast features that earned a slot in the saliency scoring.
    salient_labels = identify_salient_labels(
        scores, candidate_idx_per_final_label
    )
    if salient_labels:
        print(f"  salient (rare-but-important) slots: {sorted(salient_labels)}")

    # 7. Graph cut refinement using the shading-invariant metric for both the
    # data term and the color-contrast edge weight.
    if len(selected_palette) > 1 and GRAPHCUT_OUTER_ITERATIONS > 0:
        protected_mask = np.isin(labels, list(salient_labels)) if salient_labels else None
        labels = graphcut_smoothing(
            mesh, face_feat, selected_feat, labels,
            protected_mask=protected_mask,
        )

    # 8. Snap-to-pure for the displayed palette. Automatic and self-gating:
    # it only fires for centroids that are genuinely near-pure black/white, so
    # it preserves figurine eyes/outlines without being hardcoded to figurines
    # and without affecting general objects that have no such colors.
    displayed_palette, snapped_labels = snap_extreme_to_pure(selected_palette)

    labels = remove_small_regions(
        mesh,
        labels,
        len(selected_palette),
        snapped_labels=snapped_labels,
        salient_labels=salient_labels,
    )

    # 9. Compact (drop unused slots) and remap all label-index sets.
    # compact_palette_and_labels may renumber labels, so salient_labels and
    # snapped_labels must be remapped or they will silently protect the wrong
    # (now non-existent) slots during voxel remesh label transfer.
    displayed_palette, labels, (salient_labels, snapped_labels) = \
        compact_palette_labels_and_sets(displayed_palette, labels,
                                        salient_labels, snapped_labels)

    return displayed_palette, labels.astype(np.uint32), salient_labels


# ---------------------------------------------------------------------------
# Graph-cut style label refinement (binary alpha-expansion over PyMaxflow)
# ---------------------------------------------------------------------------

def graphcut_smoothing(mesh, face_feat, palette_feat, init_labels,
                       smoothness=None,
                       max_outer_iter=None,
                       crease_angle_deg=None,
                       protected_mask=None):
    """Refine per-face labels by minimizing a CRF energy on the face graph.

    `face_feat` / `palette_feat` are vectors in the shading-invariant feature
    space (see shading_invariant_features). Each outer iteration cycles through
    every label as 'alpha' and runs a binary expansion (PyMaxflow): each
    non-alpha face decides whether to switch to alpha, balancing data cost
    (feature distance to the palette color) against smoothness cost (label
    disagreement with neighbors). Pairwise weights are scaled down across
    creases (high dihedral angle) AND across high color-contrast edges, so
    color boundaries land on geometric or texture edges.
    """
    if smoothness is None:
        smoothness = SMOOTHNESS_WEIGHT
    if max_outer_iter is None:
        max_outer_iter = GRAPHCUT_OUTER_ITERATIONS
    if crease_angle_deg is None:
        crease_angle_deg = CREASE_ANGLE_DEG

    n_faces = len(mesh.faces)
    n_labels = len(palette_feat)
    if n_labels <= 1 or n_faces == 0:
        return np.asarray(init_labels, dtype=np.uint32)

    if protected_mask is None:
        protected_mask = np.zeros(n_faces, dtype=bool)

    diff = face_feat[:, None, :] - palette_feat[None, :, :]
    data_costs = np.sum(diff * diff, axis=2)
    if data_costs.max() > 0:
        data_costs = data_costs / data_costs.max() * 100.0

    labels = np.asarray(init_labels, dtype=np.int32).copy()

    adjacency = np.asarray(mesh.face_adjacency)
    if len(adjacency) == 0:
        return labels.astype(np.uint32)

    try:
        angles = np.asarray(mesh.face_adjacency_angles, dtype=np.float64)
    except Exception:
        angles = np.zeros(len(adjacency), dtype=np.float64)

    ea = adjacency[:, 0].astype(np.int64)
    eb = adjacency[:, 1].astype(np.int64)
    # Geometric crease term: high dihedral angle → low penalty (cut welcome).
    geom_weight = np.exp(-angles / np.deg2rad(crease_angle_deg))
    # Color-contrast term: large feature distance between adjacent faces → low
    # penalty, so the graph cut can follow hue edges even on smooth surfaces
    # while ignoring pure shading gradients (which are small in this space).
    color_diff = np.linalg.norm(
        face_feat[ea] - face_feat[eb], axis=1
    )
    color_weight = np.exp(-color_diff / COLOR_CONTRAST_SIGMA)
    edge_weights = geom_weight * color_weight
    pair_costs = (smoothness * edge_weights).astype(np.float64)

    rng = np.random.default_rng(42)
    INF = np.float64(1e10)

    outer_bar = tqdm(range(max_outer_iter), desc="  graph-cut", unit="iter")
    for _ in outer_bar:
        any_change = False
        inner_bar = tqdm(
            rng.permutation(n_labels),
            desc="    alpha", unit="label",
            leave=False, total=n_labels
        )
        for alpha in inner_bar:
            inner_bar.set_postfix(alpha=alpha)
            stay_costs = data_costs[np.arange(n_faces), labels].astype(np.float64)
            switch_costs = data_costs[:, alpha].astype(np.float64)
            already_alpha = labels == alpha
            force_stay = already_alpha | protected_mask

            src_caps = np.where(force_stay, INF, stay_costs)
            sink_caps = np.where(force_stay, 0.0, switch_costs)

            g = maxflow.Graph[float]()
            node_ids = g.add_nodes(n_faces)

            try:
                g.add_grid_tedges(node_ids, src_caps, sink_caps)
            except (AttributeError, TypeError):
                add_tedge = g.add_tedge
                for i in range(n_faces):
                    add_tedge(int(node_ids[i]),
                              float(src_caps[i]),
                              float(sink_caps[i]))

            try:
                g.add_edges(node_ids[ea], node_ids[eb], pair_costs, pair_costs)
            except (AttributeError, TypeError):
                add_edge = g.add_edge
                for i in range(len(adjacency)):
                    add_edge(int(node_ids[int(ea[i])]),
                             int(node_ids[int(eb[i])]),
                             float(pair_costs[i]),
                             float(pair_costs[i]))

            g.maxflow()

            try:
                segments = np.asarray(g.get_grid_segments(node_ids))
            except (AttributeError, TypeError):
                get_seg = g.get_segment
                segments = np.fromiter(
                    (get_seg(int(node_ids[i])) for i in range(n_faces)),
                    dtype=np.int8, count=n_faces,
                )

            switch = (segments == 0) & ~force_stay
            if switch.any():
                labels[switch] = alpha
                any_change = True

        outer_bar.set_postfix(changed=any_change)
        if not any_change:
            break

    return labels.astype(np.uint32)


def remove_small_regions(mesh, labels, n_labels,
                         snapped_labels=None,
                         salient_labels=None):
    """Geometry-aware removal of tiny connected face regions.

    Threshold per slot:
      - SALIENT_MIN_REGION_FACES for slots whose source candidate was
        rare-but-important (low area + high contrast/compactness/recon).
      - SNAPPED_MIN_REGION_FACES for slots displayed as pure black/white
        after the cosmetic snap.
      - FREE_MIN_REGION_FACES for everything else, to clean up speckle
        noise from clustering.

    Replacement label = most common neighboring label.
    """
    labels = np.asarray(labels, dtype=np.int32).copy()
    if snapped_labels is None:
        snapped_labels = set()
    if salient_labels is None:
        salient_labels = set()

    adjacency = np.asarray(mesh.face_adjacency)
    n_faces = len(labels)

    neighbors = [[] for _ in range(n_faces)]
    for a, b in adjacency:
        neighbors[int(a)].append(int(b))
        neighbors[int(b)].append(int(a))

    visited = np.zeros(n_faces, dtype=bool)
    for start in tqdm(range(n_faces), desc="  region cleanup", unit="face", miniters=n_faces//20):
        if visited[start]:
            continue

        label = int(labels[start])
        stack = [start]
        region = []
        border_labels = []
        visited[start] = True

        while stack:
            face_idx = stack.pop()
            region.append(face_idx)
            for nb in neighbors[face_idx]:
                if labels[nb] == label:
                    if not visited[nb]:
                        visited[nb] = True
                        stack.append(nb)
                else:
                    border_labels.append(int(labels[nb]))

        if label in salient_labels:
            min_faces = SALIENT_MIN_REGION_FACES
        elif label in snapped_labels:
            min_faces = SNAPPED_MIN_REGION_FACES
        else:
            min_faces = FREE_MIN_REGION_FACES

        if len(region) < min_faces and border_labels:
            replacement = int(np.bincount(border_labels, minlength=n_labels).argmax())
            for face_idx in region:
                labels[face_idx] = replacement

    return labels


def compact_palette_and_labels(palette, labels):
    """Remove unused palette entries and remap labels to be contiguous from 0."""
    labels = np.asarray(labels, dtype=np.uint32)
    used = np.unique(labels)
    remap = np.zeros(len(palette), dtype=np.uint32)
    for new_idx, old_idx in enumerate(used):
        remap[old_idx] = new_idx
    new_labels = remap[labels]
    new_palette = palette[used]
    return new_palette, new_labels


def compact_palette_labels_and_sets(palette, labels, *label_sets):
    """Like compact_palette_and_labels but also remaps arbitrary sets of label indices.

    Returns (new_palette, new_labels, [new_set, ...]) where each set in
    label_sets has its integer members remapped to the post-compaction indices.
    Members that were compacted away (unused labels) are silently dropped.
    """
    labels = np.asarray(labels, dtype=np.uint32)
    used = np.unique(labels)
    remap = {int(old): int(new) for new, old in enumerate(used)}
    new_labels = np.array([remap[int(x)] for x in labels], dtype=np.uint32)
    new_palette = palette[used]
    new_sets = [{remap[int(x)] for x in s if int(x) in remap} for s in label_sets]
    return new_palette, new_labels, new_sets


# ---------------------------------------------------------------------------
# Final color-boundary cleaning (color-free MRF/Potts label denoising)
# ---------------------------------------------------------------------------

def clean_label_boundaries(mesh, labels, n_labels,
                           protected_mask=None,
                           smoothness=None,
                           stay_cost=None,
                           iterations=None,
                           crease_angle_deg=None,
                           despeckle_faces=None):
    """Straighten color borders and remove speckle on the FINAL output mesh.

    Minimizes a Potts energy on the face-adjacency graph::

        E(L) = Σ_f D(f, L_f)  +  Σ_(f,g) w_fg · [L_f ≠ L_g]

    with D(f, L) = 0 if L == anchor[f] else stay_cost, and
    w_fg = smoothness · (shared_edge_len / mean_len) · exp(-dihedral / crease).

    Color-free: it only needs the label field, so it runs after voxel remesh
    (which the color-aware graph cut cannot, having no colors there). The
    edge-length weight makes the optimizer prefer short, straight boundaries;
    the crease factor lets borders still hug real geometric edges; the
    stay_cost anchor (> smoothness) preserves thin coherent lines so only
    locally-inconsistent speckle flips. Solved by α-expansion (PyMaxflow).
    Finishes with a small-region despeckle. Salient faces are never moved.
    """
    smoothness = BOUNDARY_CLEAN_SMOOTHNESS if smoothness is None else smoothness
    stay_cost = BOUNDARY_CLEAN_STAY_COST if stay_cost is None else stay_cost
    iterations = BOUNDARY_CLEAN_ITERS if iterations is None else iterations
    crease_angle_deg = (
        BOUNDARY_CLEAN_CREASE_ANGLE_DEG if crease_angle_deg is None else crease_angle_deg
    )
    despeckle_faces = (
        BOUNDARY_CLEAN_DESPECKLE_FACES if despeckle_faces is None else despeckle_faces
    )

    labels = np.asarray(labels, dtype=np.int32).copy()
    n_faces = len(labels)
    if n_labels <= 1 or n_faces == 0:
        return labels.astype(np.uint32)

    adjacency = np.asarray(mesh.face_adjacency)
    if len(adjacency) == 0:
        return labels.astype(np.uint32)

    if protected_mask is None:
        protected_mask = np.zeros(n_faces, dtype=bool)
    else:
        protected_mask = np.asarray(protected_mask, dtype=bool)

    anchor = labels.copy()

    ea = adjacency[:, 0].astype(np.int64)
    eb = adjacency[:, 1].astype(np.int64)

    # Shared-edge length per adjacent face pair (prefer short, straight cuts).
    try:
        edge_vi = np.asarray(mesh.face_adjacency_edges)
        ev = mesh.vertices[edge_vi[:, 0]] - mesh.vertices[edge_vi[:, 1]]
        edge_len = np.linalg.norm(ev, axis=1)
    except Exception:
        edge_len = np.ones(len(adjacency), dtype=np.float64)
    edge_len = edge_len / max(edge_len.mean(), 1e-9)

    # Crease factor: boundaries may still follow sharp geometric edges.
    try:
        angles = np.asarray(mesh.face_adjacency_angles, dtype=np.float64)
    except Exception:
        angles = np.zeros(len(adjacency), dtype=np.float64)
    crease = np.exp(-angles / np.deg2rad(crease_angle_deg))

    pair_costs = (smoothness * edge_len * crease).astype(np.float64)

    rng = np.random.default_rng(0)
    INF = np.float64(1e10)

    outer = tqdm(range(iterations), desc="  boundary clean", unit="iter")
    for _ in outer:
        any_change = False
        for alpha in rng.permutation(n_labels):
            alpha = int(alpha)
            # Data: anchor each face to its ORIGINAL label.
            stay_costs = np.where(labels == anchor, 0.0, stay_cost)
            switch_costs = np.full(n_faces, stay_cost, dtype=np.float64)
            switch_costs[anchor == alpha] = 0.0

            already_alpha = labels == alpha
            force_stay = already_alpha | protected_mask
            src_caps = np.where(force_stay, INF, stay_costs)
            sink_caps = np.where(force_stay, 0.0, switch_costs)

            g = maxflow.Graph[float]()
            node_ids = g.add_nodes(n_faces)
            try:
                g.add_grid_tedges(node_ids, src_caps, sink_caps)
            except (AttributeError, TypeError):
                for i in range(n_faces):
                    g.add_tedge(int(node_ids[i]), float(src_caps[i]), float(sink_caps[i]))
            try:
                g.add_edges(node_ids[ea], node_ids[eb], pair_costs, pair_costs)
            except (AttributeError, TypeError):
                for i in range(len(adjacency)):
                    g.add_edge(int(node_ids[int(ea[i])]), int(node_ids[int(eb[i])]),
                               float(pair_costs[i]), float(pair_costs[i]))
            g.maxflow()
            try:
                segments = np.asarray(g.get_grid_segments(node_ids))
            except (AttributeError, TypeError):
                segments = np.fromiter(
                    (g.get_segment(int(node_ids[i])) for i in range(n_faces)),
                    dtype=np.int8, count=n_faces,
                )
            switch = (segments == 0) & ~force_stay
            if switch.any():
                labels[switch] = alpha
                any_change = True
        outer.set_postfix(changed=any_change)
        if not any_change:
            break

    # Final despeckle pass.
    if despeckle_faces > 0:
        labels = remove_small_regions(
            mesh, labels, n_labels,
            snapped_labels=set(),
            salient_labels=set() if protected_mask is None else None,
        )

    return labels.astype(np.uint32)


def print_color_report(mesh, palette, face_color_idx):
    print("\n--- Color report ---")
    n_faces = len(face_color_idx)
    counts = np.bincount(face_color_idx, minlength=len(palette))
    for i, (color, count) in enumerate(zip(palette, counts)):
        pct = 100.0 * count / n_faces if n_faces else 0
        print(
            f"  slot {i}: hex={color_hex(color)} "
            f"faces={count} ({pct:.1f}%)"
        )

    adjacency = np.asarray(mesh.face_adjacency)
    neighbors = [[] for _ in range(n_faces)]
    for a, b in adjacency:
        neighbors[int(a)].append(int(b))
        neighbors[int(b)].append(int(a))

    visited = np.zeros(n_faces, dtype=bool)
    region_sizes = {i: [] for i in range(len(palette))}
    for start in range(n_faces):
        if visited[start]:
            continue
        label = int(face_color_idx[start])
        stack = [start]
        size = 0
        visited[start] = True
        while stack:
            f = stack.pop()
            size += 1
            for nb in neighbors[f]:
                if not visited[nb] and face_color_idx[nb] == label:
                    visited[nb] = True
                    stack.append(nb)
        region_sizes[label].append(size)

    for label, sizes in region_sizes.items():
        if sizes:
            print(
                f"  slot {label}: regions={len(sizes)} "
                f"max={max(sizes)} median={int(np.median(sizes))} "
                f"p10={int(np.percentile(sizes, 10))}"
            )


# ---------------------------------------------------------------------------
# 3MF / Bambu project writing
# ---------------------------------------------------------------------------

def color_hex(color):
    return "#{:02X}{:02X}{:02X}".format(int(color[0]), int(color[1]), int(color[2]))


def format_float(value):
    return f"{float(value):.9g}"


def build_3dmodel_xml(mesh, face_color_idx):
    today = dt.date.today().isoformat()
    vertices = mesh.vertices
    faces = mesh.faces

    min_corner = vertices.min(axis=0)
    max_corner = vertices.max(axis=0)
    center = (min_corner + max_corner) / 2.0
    tx = 128.0 - center[0] * BUILD_SCALE
    ty = 128.0 - center[1] * BUILD_SCALE
    tz = -min_corner[2] * BUILD_SCALE
    transform = (
        f"{BUILD_SCALE:g} 0 0 0 {BUILD_SCALE:g} 0 0 0 {BUILD_SCALE:g} "
        f"{format_float(tx)} {format_float(ty)} {format_float(tz)}"
    )

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">',
        ' <metadata name="Application">BambuStudio-02.06.01.55</metadata>',
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>',
        ' <metadata name="Copyright"></metadata>',
        f' <metadata name="CreationDate">{today}</metadata>',
        ' <metadata name="Description"></metadata>',
        ' <metadata name="Designer"></metadata>',
        ' <metadata name="DesignerCover"></metadata>',
        ' <metadata name="DesignerUserId">1420266022</metadata>',
        ' <metadata name="License"></metadata>',
        f' <metadata name="ModificationDate">{today}</metadata>',
        ' <metadata name="Origin"></metadata>',
        ' <metadata name="ProfileCover"></metadata>',
        ' <metadata name="ProfileDescription"></metadata>',
        ' <metadata name="ProfileTitle"></metadata>',
        ' <metadata name="Title"></metadata>',
        " <resources>",
        '  <object id="1" type="model">',
        "   <mesh>",
        "    <vertices>",
    ]

    for vertex in vertices:
        lines.append(
            '     <vertex x="{}" y="{}" z="{}"/>'.format(
                format_float(vertex[0]), format_float(vertex[1]), format_float(vertex[2])
            )
        )

    lines.extend(["    </vertices>", "    <triangles>"])

    for face, color_idx in zip(faces, face_color_idx):
        paint_code = BAMBU_PAINT_CODES[int(color_idx)]
        lines.append(
            '     <triangle v1="{}" v2="{}" v3="{}" paint_color="{}"/>'.format(
                int(face[0]), int(face[1]), int(face[2]), paint_code
            )
        )

    lines.extend(
        [
            "    </triangles>",
            "   </mesh>",
            "  </object>",
            '  <object id="2" type="model">',
            "   <components>",
            '    <component objectid="1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>',
            "   </components>",
            "  </object>",
            " </resources>",
            " <build>",
            f'  <item objectid="2" transform="{transform}" printable="1"/>',
            " </build>",
            "</model>",
            "",
        ]
    )
    return "\n".join(lines), transform


def template_project_settings(palette):
    if TEMPLATE_BAMBU_PROJECT is not None and TEMPLATE_BAMBU_PROJECT.exists():
        with zipfile.ZipFile(TEMPLATE_BAMBU_PROJECT) as template:
            settings = json.loads(
                template.read("Metadata/project_settings.config").decode("utf-8", "replace")
            )
    else:
        settings = {}

    filament_colors = [color_hex(color) for color in palette]
    count = len(filament_colors)
    source_count = len(settings.get("filament_colour", [])) or count

    def resize_list(values, target_count):
        if not values:
            return values
        if len(values) >= target_count:
            return values[:target_count]
        return values + [values[-1]] * (target_count - len(values))

    for key, value in list(settings.items()):
        if not isinstance(value, list):
            continue
        if len(value) == source_count:
            settings[key] = resize_list(value, count)
        elif len(value) == source_count * 2 and key.startswith("filament_"):
            settings[key] = resize_list(value, count * 2)
        elif len(value) == source_count * 4 and key.startswith("filament_"):
            settings[key] = resize_list(value, count * 4)

    settings.update(
        {
            "filament_colour": filament_colors,
            "filament_multi_colour": filament_colors,
            "filament_colour_type": ["1"] * count,
            "filament_self_index": [str(i + 1) for i in range(count)],
            "filament_map": [str(i + 1) for i in range(count)],
            "filament_volume_map": ["0"] * count,
            "filament_type": ["PLA"] * count,
            "filament_settings_id": ["Bambu PLA Basic @BBL A1"] * count,
            "filament_vendor": ["Bambu Lab"] * count,
            "filament_diameter": ["1.75"] * count,
            "filament_density": ["1.26"] * count,
            "filament_ids": ["GFA00"] * count,
            "default_filament_colour": [""] * count,
            "flush_volumes_matrix": ["0" if i == j else "140" for i in range(count) for j in range(count)],
            "flush_volumes_vector": ["140"] * (count * 2),
            "filament_map_mode": "Auto For Flush",
            "has_filament_switcher": "1" if count > 1 else "0",
            "enable_filament_dynamic_map": "0",
        }
    )
    return json.dumps(settings, indent=4)


def build_model_settings(face_count, transform, filament_count, source_name="model.glb"):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="2">
    <metadata key="name" value="{source_name}"/>
    <metadata key="extruder" value="1"/>
    <metadata face_count="{face_count}"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="{source_name}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_file" value="{source_name}"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="source_offset_x" value="0"/>
      <metadata key="source_offset_y" value="0"/>
      <metadata key="source_offset_z" value="0"/>
      <mesh_stat face_count="{face_count}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value=""/>
    <metadata key="locked" value="false"/>
    <metadata key="filament_map_mode" value="Auto For Flush"/>
    <metadata key="filament_maps" value="{' '.join(str(i + 1) for i in range(filament_count))}"/>
    <metadata key="filament_volume_maps" value="{' '.join(['0'] * filament_count)}"/>
    <metadata key="thumbnail_file" value="Metadata/plate_1.png"/>
    <metadata key="thumbnail_no_light_file" value="Metadata/plate_no_light_1.png"/>
    <metadata key="top_file" value="Metadata/top_1.png"/>
    <metadata key="pick_file" value="Metadata/pick_1.png"/>
    <model_instance>
      <metadata key="object_id" value="2"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="1"/>
    </model_instance>
  </plate>
  <assemble>
   <assemble_item object_id="2" instance_id="0" transform="{escape(transform)}" offset="0 0 0" />
  </assemble>
</config>
'''


def write_bambu_project(mesh, palette, face_color_idx, output_file, source_name="model.glb"):
    model_xml, transform = build_3dmodel_xml(mesh, face_color_idx)
    project_settings = template_project_settings(palette)
    model_settings = build_model_settings(len(mesh.faces), transform, len(palette), source_name)
    slice_info = '''<?xml version="1.0" encoding="UTF-8"?>
<config>
  <header>
    <header_item key="X-BBL-Client-Type" value="slicer"/>
    <header_item key="X-BBL-Client-Version" value="02.06.01.55"/>
  </header>
</config>
'''
    content_types = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="gcode" ContentType="text/x.gcode"/>
</Types>
'''
    rels = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
 <Relationship Target="/Metadata/plate_1.png" Id="rel-2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"/>
 <Relationship Target="/Metadata/plate_1.png" Id="rel-4" Type="http://schemas.bambulab.com/package/2021/cover-thumbnail-middle"/>
 <Relationship Target="/Metadata/plate_1_small.png" Id="rel-5" Type="http://schemas.bambulab.com/package/2021/cover-thumbnail-small"/>
</Relationships>
'''
    plate_json = json.dumps({"bbox_all": [], "filament_ids": [], "model_ids": [2]})

    with zipfile.ZipFile(output_file, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("3D/3dmodel.model", model_xml)
        archive.writestr("Metadata/project_settings.config", project_settings)
        archive.writestr("Metadata/model_settings.config", model_settings)
        archive.writestr("Metadata/slice_info.config", slice_info)
        archive.writestr("Metadata/filament_sequence.json", '{"plate_1":{"nozzle_sequence":[],"optimal_assignment":[],"sequence":[]}}')
        archive.writestr("Metadata/cut_information.xml", '<?xml version="1.0" encoding="utf-8"?><objects><object id="1"><cut_id id="0" check_sum="1" connectors_cnt="0"/></object></objects>')
        archive.writestr("Metadata/plate_1.json", plate_json)
        for name in ("plate_1.png", "plate_1_small.png", "plate_no_light_1.png", "top_1.png", "pick_1.png"):
            archive.writestr(f"Metadata/{name}", TRANSPARENT_PNG)


# ---------------------------------------------------------------------------
# Public API — called by jobs.py via asyncio.to_thread
# ---------------------------------------------------------------------------

def convert(glb_path: str, output_path: str) -> None:
    """Convert a GLB file to a Bambu Studio 3MF. Blocking — run in a thread."""
    source_name = Path(glb_path).name
    logger.info("Starting GLB→3MF conversion: %s", glb_path)

    mesh = load_mesh(glb_path)
    print(f"  loaded: verts={len(mesh.vertices)} faces={len(mesh.faces)}")

    print("Sampling face colors")
    face_colors = sample_face_colors(mesh)

    print("Repairing mesh (basic)")
    mesh, face_colors = basic_repair_mesh(mesh, face_colors)

    if len(mesh.faces) != len(face_colors):
        raise RuntimeError(
            f"Face/color count mismatch after repair: "
            f"faces={len(mesh.faces)} colors={len(face_colors)}"
        )

    print("Choosing palette and assigning labels")
    palette, face_color_idx, salient_labels = choose_face_colors(mesh, face_colors)

    print_color_report(mesh, palette, face_color_idx)

    if not mesh.is_watertight and REMESH_MODE != "off" and should_voxel_remesh(mesh):
        if REMESH_SMOOTH_ITERS > 0 or REMESH_REPROJECT_STR > 0:
            print("\nMesh not watertight; running printer-aware voxel remesh "
                  "(+ Taubin smoothing + reprojection)")
        else:
            print("\nMesh not watertight; running printer-aware voxel remesh")
        mesh, face_color_idx = voxel_remesh_with_label_transfer(
            mesh, face_color_idx, salient_labels=salient_labels
        )

    if BOUNDARY_CLEAN_ENABLE and len(palette) > 1:
        print("\nCleaning color boundaries (final MRF label regularization)")
        protected = (
            np.isin(face_color_idx, list(salient_labels)) if salient_labels else None
        )
        face_color_idx = clean_label_boundaries(
            mesh, face_color_idx, len(palette), protected_mask=protected
        )
        print_color_report(mesh, palette, face_color_idx)

    write_bambu_project(mesh, palette, face_color_idx, output_path, source_name)

    logger.info(
        "3MF written: %s  colors: %s",
        output_path,
        ", ".join(color_hex(c) for c in palette),
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        convert(sys.argv[1], sys.argv[2])
    else:
        # CLI fallback using env-var globals (original behaviour)
        mesh = load_mesh(INPUT_FILE)
        face_colors = sample_face_colors(mesh)
        mesh, face_colors = basic_repair_mesh(mesh, face_colors)
        palette, face_color_idx, salient_labels = choose_face_colors(mesh, face_colors)
        print_color_report(mesh, palette, face_color_idx)
        if not mesh.is_watertight and REMESH_MODE != "off" and should_voxel_remesh(mesh):
            mesh, face_color_idx = voxel_remesh_with_label_transfer(
                mesh, face_color_idx, salient_labels=salient_labels
            )
        if BOUNDARY_CLEAN_ENABLE and len(palette) > 1:
            protected = np.isin(face_color_idx, list(salient_labels)) if salient_labels else None
            face_color_idx = clean_label_boundaries(
                mesh, face_color_idx, len(palette), protected_mask=protected
            )
        write_bambu_project(mesh, palette, face_color_idx, OUTPUT_FILE)
        print("\nDONE:", OUTPUT_FILE)
        print("Filament colors:", ", ".join(color_hex(color) for color in palette))
