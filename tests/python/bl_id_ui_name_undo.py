# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Run in a fresh foreground Blender to check actual undo and redo, then quit."""

import argparse
import json
from pathlib import Path
import sys
import traceback

import bpy


def run_checks():
    """Use Blender's undo stack; read restored items again after every operation."""
    window = bpy.context.window_manager.windows[0]
    area = next(area for area in window.screen.areas if area.type == 'VIEW_3D')
    region = next(region for region in area.regions if region.type == 'WINDOW')
    bpy.context.preferences.edit.use_global_undo = True
    with bpy.context.temp_override(window=window, area=area, region=region):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_cube_add()
        item = bpy.context.active_object
        source = "Undo UI Name Source"
        personal = "Undo UI Name Personal"
        item.name = source
        item.ui_name_translation_mark()
        assert item.ui_name_is_translatable
        assert item.ui_name == "Vật thể hoàn tác thử nghiệm"
        assert bpy.ops.ed.undo_push(message="Marked name") == {'FINISHED'}
        item.name = personal
        assert not item.ui_name_is_translatable
        assert bpy.ops.ed.undo_push(message="Literal renamed name") == {'FINISHED'}
        assert bpy.ops.ed.undo() == {'FINISHED'}
        item = bpy.data.objects[source]
        assert item.ui_name_is_translatable
        assert item.ui_name == "Vật thể hoàn tác thử nghiệm"
        assert bpy.ops.ed.redo() == {'FINISHED'}
        item = bpy.data.objects[personal]
        assert not item.ui_name_is_translatable
        assert item.ui_name == personal

        item.name = source
        item.ui_name_translation_mark()
        assert bpy.ops.ed.undo_push(message="Before duplicate") == {'FINISHED'}
        assert bpy.ops.object.duplicate() == {'FINISHED'}
        duplicate = bpy.context.active_object
        assert duplicate.name == source + ".001"
        assert not duplicate.ui_name_is_translatable
        assert bpy.data.objects[source].ui_name_is_translatable
        assert bpy.data.objects[source].ui_name == "Vật thể hoàn tác thử nghiệm"
        # Timer-driven Python calls need an explicit checkpoint, unlike a UI operator event.
        assert bpy.ops.ed.undo_push(message="After duplicate") == {'FINISHED'}
        assert bpy.ops.ed.undo() == {'FINISHED'}
        assert bpy.data.objects.get(source + ".001") is None
        assert bpy.data.objects[source].ui_name_is_translatable
        assert bpy.ops.ed.redo() == {'FINISHED'}
        assert not bpy.data.objects[source + ".001"].ui_name_is_translatable

        first = bpy.data.objects[source]
        second = bpy.data.objects[source + ".001"]
        first.ui_name_translation_mark()
        second.ui_name_translation_mark()
        assert bpy.ops.ed.undo_push(message="Before forced name collision") == {'FINISHED'}
        first.rename(second.name, mode='ALWAYS')
        assert not first.ui_name_is_translatable
        assert not second.ui_name_is_translatable
        collision_names = (first.name, second.name)
        assert bpy.ops.ed.undo_push(message="After forced name collision") == {'FINISHED'}
        assert bpy.ops.ed.undo() == {'FINISHED'}
        assert bpy.data.objects[source].ui_name_is_translatable
        assert bpy.data.objects[source + ".001"].ui_name_is_translatable
        assert bpy.ops.ed.redo() == {'FINISHED'}
        for name in collision_names:
            assert not bpy.data.objects[name].ui_name_is_translatable
            assert bpy.data.objects[name].ui_name == name
    return ["rename undo/redo", "duplicate undo/redo", "forced collision undo/redo"]


def main():
    has_arguments = "--" in sys.argv
    arguments = sys.argv[sys.argv.index("--") + 1:] if has_arguments else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(arguments)

    def check_and_quit():
        view = bpy.context.preferences.view
        original_preferences = (view.language, view.use_translate_interface)
        bpy.app.translations.register("blender_ui_name_undo", {
            "vi_VN": {("Object", "Undo UI Name Source"): "Vật thể hoàn tác thử nghiệm"},
        })
        view.language = 'vi_VN'
        view.use_translate_interface = True
        try:
            checks = run_checks()
            report = {"passed": True, "checks": checks, "binary": bpy.app.binary_path}
        except Exception:
            report = {"passed": False, "error": traceback.format_exc(), "binary": bpy.app.binary_path}
            sys.stderr.write(report["error"])
        finally:
            bpy.app.translations.unregister("blender_ui_name_undo")
            view.language, view.use_translate_interface = original_preferences
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        bpy.ops.wm.quit_blender()
        return None

    bpy.app.timers.register(check_and_quit, first_interval=2.0)


is_main_module = __name__ == "__main__"
if is_main_module:
    main()
