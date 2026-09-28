# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Generate legacy fixtures with Blender 4.5.9, never with a patched build.

blender --background --factory-startup --python generate_legacy.py
"""

import json
from pathlib import Path

import bpy

assert bpy.app.version == (4, 5, 9)
assert "label_source" not in bpy.types.WorkSpace.bl_rna.properties
assert "custom_display_name" not in bpy.types.WorkSpace.bl_rna.properties
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.use_preferences_save = False
bpy.context.preferences.filepaths.file_preview_type = 'NONE'
bpy.context.preferences.filepaths.save_version = 0
directory = Path(__file__).resolve().parent
fixtures = []
for localized in (False, True):
    if localized:
        bpy.data.workspaces["Layout"].name = "B\u1ed1 c\u1ee5c.001"
        bpy.data.workspaces["Modeling"].name = "T\u00f9y ch\u1ec9nh"
    filename = "legacy_localized.blend" if localized else "legacy_english.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(directory / filename), check_existing=False, compress=True)
    fixtures.append({"path": filename, "workspace_names": sorted(bpy.data.workspaces.keys())})
manifest = {"producer_version": bpy.app.version_string,
            "producer_hash": bpy.app.build_hash.decode("ascii"), "fixtures": fixtures}
(directory / "legacy.json").write_text(json.dumps(manifest, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
