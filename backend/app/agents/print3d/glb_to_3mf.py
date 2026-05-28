"""GLB → Bambu Studio 3MF converter.

Vendored from ~/Downloads/glb_to_3mf_package/glb_to_3mf.py.
Public API: convert(glb_path, output_path) — thread-safe, blocking.
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

logger = logging.getLogger(__name__)

INPUT_FILE = "input.glb"
OUTPUT_FILE = "output.3mf"
TEMPLATE_BAMBU_PROJECT = Path("")  # no template — always use empty-dict fallback
NUM_COLORS = 4
BUILD_SCALE = 100.0
SMOOTHING_ITERATIONS = 4
MIN_REGION_FACES = 25
MODE = "figurine"
BLACK_THRESHOLD = 40
WHITE_THRESHOLD = 220
LOCKED_MIN_REGION_FACES = 12
FREE_MIN_REGION_FACES = 45

BAMBU_PAINT_CODES = ["4", "8", "0C", "1C", "2C", "3C", "4C", "5C"]
TRANSPARENT_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADElEQVR42mP8z8BQDwAF"
    "gwJ/lv0Z2wAAAABJRU5ErkJggg=="
)


def extract_colors(mesh):
    if hasattr(mesh.visual, "vertex_colors") and len(mesh.visual.vertex_colors) > 0:
        return mesh.visual.vertex_colors[:, :3]

    material = getattr(mesh.visual, "material", None)
    texture = getattr(material, "image", None)
    if texture is None:
        texture = getattr(material, "baseColorTexture", None)

    if hasattr(mesh.visual, "uv") and texture is not None:
        uv = mesh.visual.uv
        image = np.array(texture)

        h, w = image.shape[:2]
        px = np.clip((uv[:, 0] * (w - 1)).astype(int), 0, w - 1)
        py = np.clip(((1 - uv[:, 1]) * (h - 1)).astype(int), 0, h - 1)

        return image[py, px][:, :3]

    base_color = getattr(material, "baseColorFactor", None)
    if base_color is not None:
        base_color = np.array(base_color[:3], dtype=float)
        if base_color.max() <= 1.0:
            base_color *= 255
        return np.tile(base_color.astype(np.uint8), (len(mesh.vertices), 1))

    mesh.visual = mesh.visual.to_color()
    return mesh.visual.vertex_colors[:, :3]


def load_mesh(path):
    scene = trimesh.load(path)
    if isinstance(scene, trimesh.Scene):
        mesh = trimesh.util.concatenate(scene.dump())
    else:
        mesh = scene
    mesh.remove_unreferenced_vertices()
    return mesh


def choose_face_colors(mesh):
    colors = extract_colors(mesh)
    if MODE == "figurine":
        return choose_face_colors_figurine(mesh, colors)

    return choose_face_colors_general(mesh, colors)


def choose_face_colors_general(mesh, colors):
    unique_colors = np.unique(colors, axis=0)
    num_clusters = min(NUM_COLORS, len(unique_colors), len(BAMBU_PAINT_CODES))

    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init="auto")
    kmeans.fit(unique_colors)
    labels = kmeans.predict(colors)
    palette = kmeans.cluster_centers_.astype(np.uint8)

    luminance = palette @ np.array([0.2126, 0.7152, 0.0722])
    order = np.argsort(luminance)
    remap = np.zeros(num_clusters, dtype=np.uint32)
    remap[order] = np.arange(num_clusters)
    palette = palette[order]
    labels = remap[labels]

    face_labels = labels[mesh.faces]
    face_color_idx = np.array(
        [np.bincount(face, minlength=num_clusters).argmax() for face in face_labels],
        dtype=np.uint32,
    )
    face_color_idx = smooth_face_labels(mesh, face_color_idx, num_clusters)
    return palette, face_color_idx


def choose_face_colors_figurine(mesh, colors):
    max_colors = min(NUM_COLORS, len(BAMBU_PAINT_CODES))
    black_mask = np.all(colors <= BLACK_THRESHOLD, axis=1)
    white_mask = np.all(colors >= WHITE_THRESHOLD, axis=1)

    locked_colors = []
    locked_masks = []
    if black_mask.any():
        locked_colors.append([0, 0, 0])
        locked_masks.append(black_mask)
    if white_mask.any() and len(locked_colors) < max_colors:
        locked_colors.append([255, 255, 255])
        locked_masks.append(white_mask)

    locked_mask = np.zeros(len(colors), dtype=bool)
    for mask in locked_masks:
        locked_mask |= mask

    free_colors = colors[~locked_mask]
    remaining_slots = max_colors - len(locked_colors)

    if remaining_slots > 0 and len(free_colors) > 0:
        unique_free_colors = np.unique(free_colors, axis=0)
        free_clusters = min(remaining_slots, len(unique_free_colors))
        kmeans = KMeans(n_clusters=free_clusters, random_state=42, n_init="auto")
        kmeans.fit(unique_free_colors)
        free_labels = kmeans.predict(free_colors) + len(locked_colors)
        free_palette = kmeans.cluster_centers_.astype(np.uint8)

        luminance = free_palette @ np.array([0.2126, 0.7152, 0.0722])
        order = np.argsort(luminance)
        remap = np.zeros(free_clusters, dtype=np.uint32)
        remap[order] = np.arange(free_clusters)
        free_palette = free_palette[order]
        free_labels = remap[free_labels - len(locked_colors)] + len(locked_colors)
    else:
        free_palette = np.empty((0, 3), dtype=np.uint8)
        free_labels = np.empty(len(free_colors), dtype=np.uint32)

    palette = np.vstack(
        [
            np.array(locked_colors, dtype=np.uint8).reshape(-1, 3),
            free_palette,
        ]
    )
    labels = np.zeros(len(colors), dtype=np.uint32)

    for locked_idx, mask in enumerate(locked_masks):
        labels[mask] = locked_idx
    labels[~locked_mask] = free_labels

    face_labels = labels[mesh.faces]
    face_color_idx = np.array(
        [np.bincount(face, minlength=len(palette)).argmax() for face in face_labels],
        dtype=np.uint32,
    )

    locked_face_mask = np.any(locked_mask[mesh.faces], axis=1)
    face_color_idx = smooth_face_labels(
        mesh,
        face_color_idx,
        len(palette),
        protected_mask=locked_face_mask,
        protected_labels=set(range(len(locked_colors))),
    )
    return palette, face_color_idx


def smooth_face_labels(mesh, labels, num_clusters, protected_mask=None, protected_labels=None):
    labels = labels.copy()
    adjacency = mesh.face_adjacency
    if protected_mask is None:
        protected_mask = np.zeros(len(labels), dtype=bool)
    if protected_labels is None:
        protected_labels = set()

    neighbors = [[] for _ in range(len(mesh.faces))]
    for a, b in adjacency:
        neighbors[int(a)].append(int(b))
        neighbors[int(b)].append(int(a))

    for _ in range(SMOOTHING_ITERATIONS):
        updated = labels.copy()
        for face_idx, face_neighbors in enumerate(neighbors):
            if protected_mask[face_idx]:
                continue
            if len(face_neighbors) < 2:
                continue
            counts = np.bincount(labels[face_neighbors], minlength=num_clusters)
            best = int(counts.argmax())
            if best != labels[face_idx] and counts[best] >= 2:
                updated[face_idx] = best
        labels = updated

    visited = np.zeros(len(labels), dtype=bool)
    for start in range(len(labels)):
        if visited[start]:
            continue

        label = labels[start]
        stack = [start]
        region = []
        border_labels = []
        visited[start] = True

        while stack:
            face_idx = stack.pop()
            region.append(face_idx)
            for neighbor in neighbors[face_idx]:
                if labels[neighbor] == label:
                    if not visited[neighbor]:
                        visited[neighbor] = True
                        stack.append(neighbor)
                else:
                    border_labels.append(labels[neighbor])

        min_faces = (
            LOCKED_MIN_REGION_FACES
            if int(label) in protected_labels
            else max(MIN_REGION_FACES, FREE_MIN_REGION_FACES)
        )
        if len(region) < min_faces and border_labels:
            replacement = np.bincount(border_labels, minlength=num_clusters).argmax()
            labels[region] = replacement

    return labels


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
    if TEMPLATE_BAMBU_PROJECT.exists():
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
            "filament_map": ["1"] * count,
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
    <metadata key="filament_maps" value="{' '.join(['1'] * filament_count)}"/>
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


def convert(glb_path: str, output_path: str) -> None:
    """Convert a GLB file to a Bambu Studio 3MF. Blocking — run in a thread."""
    source_name = Path(glb_path).name
    mesh = load_mesh(glb_path)
    palette, face_color_idx = choose_face_colors(mesh)
    write_bambu_project(mesh, palette, face_color_idx, output_path, source_name)
    logger.info("3MF written: %s  colors: %s", output_path, ", ".join(color_hex(c) for c in palette))


if __name__ == "__main__":
    convert(INPUT_FILE, OUTPUT_FILE)
