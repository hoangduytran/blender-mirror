# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Print real workspace, Sculpt brush, node-tool and asset presentation examples.

Run with the rebuilt Blender's --background --factory-startup --python.
This prints API evidence; it does not claim visible screen verification.
"""

import json

import bpy


def demonstrate_names():
    view = bpy.context.preferences.view
    previous = (view.language, view.use_translate_interface, view.use_translate_new_dataname)
    module = "ui_name_review_asset_example"
    bpy.app.translations.register(module, {
        "vi_VN": {("Object", "Review reusable object"): "Vật thể dùng lại thử nghiệm"},
    })
    try:
        workspace = bpy.context.workspace
        assert workspace.ui_name_is_translatable
        assert bpy.ops.object.mode_set(mode='SCULPT') == {'FINISHED'}
        assert bpy.ops.brush.asset_activate(
            asset_library_type='ESSENTIALS',
            relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth',
        ) == {'FINISHED'}
        brush = bpy.context.tool_settings.sculpt.brush
        group = bpy.data.node_groups.new("Round", 'GeometryNodeTree')
        group.is_tool = True
        group.asset_mark()
        group.ui_name_translation_mark()
        asset = bpy.data.objects.new("Review reusable object", None)
        asset.asset_mark()
        asset.ui_name_translation_mark()
        rows = []
        for kind, item in (("workspace", workspace), ("Sculpt brush", brush),
                           ("node tool", group), ("asset", asset)):
            source = item.name
            view.use_translate_interface = True
            view.use_translate_new_dataname = True
            view.language = 'en_US'
            default = item.ui_name
            view.language = 'vi_VN'
            translated = item.ui_name
            view.use_translate_interface = False
            disabled = item.ui_name
            assert item.name == source
            assert default == source and disabled == source
            rows.append({"kind": kind, "stored_name": source, "English": default,
                         "Vietnamese": translated, "translation_off": disabled,
                         "context": item.ui_name_translation_context,
                         "eligible": item.ui_name_is_translatable,
                         "catalog": "supplied test entry" if item == asset else "installed Blender"})
        view.use_translate_interface = True
        asset.name = "My reusable object"
        assert not asset.ui_name_is_translatable
        assert asset.ui_name == asset.name
        asset.name = "Review reusable object"
        assert not asset.ui_name_is_translatable
        assert asset.ui_name == asset.name
        print(json.dumps({"presentation_examples": rows,
                          "asset_rename_back": asset.ui_name,
                          "rename_back_eligible": asset.ui_name_is_translatable,
                          "visible_screen_check": False}, ensure_ascii=False, indent=2))
    finally:
        bpy.app.translations.unregister(module)
        view.language, view.use_translate_interface, view.use_translate_new_dataname = previous


is_main_module = __name__ == "__main__"
if is_main_module:
    demonstrate_names()
