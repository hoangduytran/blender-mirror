# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Foreground review fixture: real shared ID selectors, editable names and workspace tabs."""

import argparse
import json
from pathlib import Path
import sys

import bpy


CASES = (
    ("review_workspace", "WorkSpace", "Review Workspace Source", "Không gian mẫu"),
    ("review_brush", "Brush", "Review Brush Source", "Cọ mẫu"),
    ("review_node_group", "NodeTree", "Review Node Tool Source", "Nhóm nút mẫu"),
    ("review_asset", "Object", "Review Asset Source", "Tài nguyên mẫu"),
)
REPORT_DIRECTORY = None
EXTERNAL_SOURCE_NAME = "Review External Asset Source"


def record(stage):
    rows = []
    for prop, _, _, _ in CASES:
        item = getattr(bpy.context.scene, prop)
        rows.append({"kind": prop, "stored": item.name, "display": item.ui_name,
                     "eligible": item.ui_name_is_translatable})
    report = {"stage": stage, "binary": bpy.app.binary_path,
              "language": bpy.context.preferences.view.language, "items": rows,
              "external_asset_imported": EXTERNAL_SOURCE_NAME in bpy.data.objects}
    (REPORT_DIRECTORY / (stage + ".json")).write_text(json.dumps(report, indent=2) + "\n")


class REVIEW_OT_language(bpy.types.Operator):
    bl_idname = "review.ui_name_language"
    bl_label = "Switch Review Language"
    language: bpy.props.StringProperty()

    def execute(self, context):
        context.preferences.view.language = self.language
        context.preferences.view.use_translate_interface = True
        record(self.language)
        return {'FINISHED'}


class REVIEW_OT_rename(bpy.types.Operator):
    bl_idname = "review.ui_name_rename"
    bl_label = "Give All Four Personal Names"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for prop, _, source, _ in CASES:
            item = getattr(context.scene, prop)
            item.name = "Personal " + source
            assert not item.ui_name_is_translatable
            assert item.ui_name == item.name
        record("renamed")
        return {'FINISHED'}


class REVIEW_OT_reopen(bpy.types.Operator):
    bl_idname = "review.ui_name_reopen"
    bl_label = "Save and Reopen Review Copy"

    def execute(self, context):
        filepath = str(REPORT_DIRECTORY / "review.blend")
        bpy.ops.wm.save_as_mainfile(filepath=filepath)
        bpy.ops.wm.open_mainfile(filepath=filepath, load_ui=False)
        record("reopened")
        return {'FINISHED'}


class REVIEW_PT_ui_names(bpy.types.Panel):
    bl_label = "Shared Display Name Review"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Name Review"

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator("review.ui_name_language", text="English", translate=False).language = 'en_US'
        row.operator("review.ui_name_language", text="Vietnamese", translate=False).language = 'vi_VN'
        for prop, _, _, _ in CASES:
            item = getattr(context.scene, prop)
            box = layout.box()
            # These call Blender's real generic selectors. Do not draw item.ui_name ourselves.
            box.template_ID(context.scene, prop)
            box.label(text="Stored name: " + item.name, translate=False)
            box.prop(item, "name", text="Edit name", translate=False)
            box.prop(item, "ui_name_is_translatable", text="Eligible", translate=False)
        layout.operator("review.ui_name_rename", translate=False)
        layout.operator("review.ui_name_reopen", translate=False)


def main():
    global REPORT_DIRECTORY
    has_arguments = "--" in sys.argv
    arguments = sys.argv[sys.argv.index("--") + 1:] if has_arguments else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--with-external-library", action='store_true',
                        help="Create a separate asset file and register Name Review External.")
    args = parser.parse_args(arguments)
    REPORT_DIRECTORY = args.output_dir.resolve()
    REPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for cls in (REVIEW_OT_language, REVIEW_OT_rename, REVIEW_OT_reopen, REVIEW_PT_ui_names):
        bpy.utils.register_class(cls)
    bpy.types.Scene.review_workspace = bpy.props.PointerProperty(type=bpy.types.WorkSpace)
    bpy.types.Scene.review_brush = bpy.props.PointerProperty(type=bpy.types.Brush)
    bpy.types.Scene.review_node_group = bpy.props.PointerProperty(type=bpy.types.NodeTree)
    bpy.types.Scene.review_asset = bpy.props.PointerProperty(type=bpy.types.Object)
    scene = bpy.context.scene
    scene.review_workspace = bpy.context.workspace
    scene.review_workspace.name = CASES[0][2]
    scene.review_brush = bpy.data.brushes.new(CASES[1][2], mode='SCULPT')
    scene.review_node_group = bpy.data.node_groups.new(CASES[2][2], 'GeometryNodeTree')
    scene.review_node_group.is_tool = True
    scene.review_node_group.is_mode_object = True
    scene.review_node_group.is_type_mesh = True
    scene.review_node_group.node_tool_idname = "geometry.review_ui_name_gui"
    assert scene.review_node_group.node_tool_idname == "geometry.review_ui_name_gui"
    scene.review_node_group.asset_mark()
    scene.review_asset = bpy.data.objects.new(CASES[3][2], None)
    scene.review_asset.asset_mark()
    scene.collection.objects.link(scene.review_asset)
    catalog = {}
    for prop, context, source, translated in CASES:
        item = getattr(scene, prop)
        item.use_fake_user = True
        item.ui_name_translation_mark()
        catalog[(context, source)] = translated
    creates_external_library = args.with_external_library
    if creates_external_library:
        library_directory = REPORT_DIRECTORY / "external"
        library_directory.mkdir(exist_ok=True)
        asset = bpy.data.objects.new(EXTERNAL_SOURCE_NAME, None)
        asset.asset_mark()
        asset.ui_name_translation_mark()
        bpy.data.libraries.write(str(library_directory / "review-external.blend"), {asset},
                                 fake_user=True)
        bpy.data.objects.remove(asset)
        bpy.context.preferences.filepaths.asset_libraries.new(
            name="Name Review External", directory=str(library_directory))
        catalog[("Object", EXTERNAL_SOURCE_NAME)] = "Tài nguyên ngoài mẫu"
        assert EXTERNAL_SOURCE_NAME not in bpy.data.objects
    bpy.app.translations.register("blender_ui_name_gui_review", {"vi_VN": catalog})
    bpy.context.preferences.view.language = 'en_US'
    bpy.context.preferences.view.use_translate_interface = True
    for area in bpy.context.screen.areas:
        is_viewport = area.type == 'VIEW_3D'
        if is_viewport:
            area.spaces.active.show_region_ui = True
    record("initial")


is_main_module = __name__ == "__main__"
if is_main_module:
    main()
