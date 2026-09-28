# SPDX-FileCopyrightText: 2025 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
This file does not run anything, its methods are accessed for tests by ``run_blender_setup.py``.
"""
import modules.ui_test_utils as ui


def _label_screenshot(name):
    import os
    from pathlib import Path
    import bpy

    directory = os.environ.get("BLENDER_TEST_WORKSPACE_SCREENSHOTS")
    has_output_directory = bool(directory)
    if has_output_directory:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        # A background/occluded test window may still hold an older displayed frame.
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=2)
        bpy.ops.screen.screenshot(filepath=str(path / (name + ".png")))


def label_modes_follow_language():
    import datetime
    import itertools
    import bpy

    e, t, window = ui.test_window()
    view = bpy.context.preferences.view
    ws = bpy.data.workspaces["Layout"]
    t.assertTrue(bpy.app.build_options.international)
    t.assertEqual(ws.label_source, 'CANONICAL')
    baseline = tuple((item.as_pointer(), item.name) for item in bpy.data.workspaces)
    active = window.workspace.as_pointer()
    previous = (view.language, view.use_translate_interface, view.use_translate_new_dataname)
    try:
        for interface, new_data in itertools.product((False, True), repeat=2):
            for language in ('en_US', 'vi_VN', 'en_US'):
                view.language = language
                # A language change can enable translation options in factory preferences.
                view.use_translate_interface = interface
                view.use_translate_new_dataname = new_data
                yield e.cursor_position_set(100, 100, move=True)
                yield datetime.timedelta(seconds=0.1)
                t.assertEqual(tuple((item.as_pointer(), item.name) for item in bpy.data.workspaces), baseline)
                t.assertEqual(window.workspace.as_pointer(), active)
                expected = bpy.app.translations.pgettext_iface(ws.name, bpy.app.translations.contexts.id_workspace)
                t.assertEqual(ws.display_name, expected)
                t.assertEqual(ws.display_mode, 'USE_TRANSLATED' if interface else 'USE_DEFAULT')
                requires_distinct_translation = interface and language == 'vi_VN'
                if requires_distinct_translation:
                    t.assertNotEqual(ws.display_name, ws.name, "A distinct Vietnamese catalog entry is required")
                    _label_screenshot("translated-tabs")
        view.use_translate_interface = True
        for custom in ("My CAD Workspace", "B\u1ed1 c\u1ee5c c\u1ee7a t\u00f4i", ""):
            ws.custom_display_name = custom
            for language in ('vi_VN', 'en_US'):
                view.language = language
                yield e.cursor_position_set(100, 100, move=True)
                yield datetime.timedelta(seconds=0.1)
                has_custom_label = bool(custom)
                expected = custom or bpy.app.translations.pgettext_iface(
                    ws.name, bpy.app.translations.contexts.id_workspace)
                t.assertEqual(ws.display_name, expected)
                t.assertEqual(ws.display_mode, 'USE_USERDEFINED' if has_custom_label else 'USE_TRANSLATED')
                t.assertEqual((ws.name, ws.label_source), ("Layout", 'CANONICAL'))
                t.assertEqual(window.workspace.as_pointer(), active)
            has_custom_label = bool(custom)
            if has_custom_label:
                _label_screenshot("custom-tabs")
        _label_screenshot("reset-tabs")
    finally:
        ws.custom_display_name = ""
        view.language, view.use_translate_interface, view.use_translate_new_dataname = previous


def label_tab_editing():
    import datetime
    import bpy

    e, t, window = ui.test_window()
    ws = bpy.data.workspaces["Layout"]
    area = ui.get_window_area_by_type(window, 'VIEW_3D')
    old_type = area.type
    view = bpy.context.preferences.view
    previous = (view.language, view.use_translate_interface)

    def draw_tabs(self, context):
        # The same ID-tab widget as the top bar, in a region the test API can target.
        self.layout.template_ID_tabs(context.window, "workspace")

    bpy.types.CONSOLE_HT_header.append(draw_tabs)
    try:
        area.type = 'CONSOLE'
        view.language = 'vi_VN'
        view.use_translate_interface = True
        yield e.cursor_position_set(100, 100, move=True)
        yield datetime.timedelta(seconds=0.2)
        region = next(region for region in area.regions if region.type == 'HEADER')

        def edit_tab():
            with bpy.context.temp_override(window=window, area=area, region=region):
                xy = bpy.context.window_manager.try_activate_rna_button(region, window, "workspace", 'TEXT_EDITING')
            t.assertTrue(xy)
            yield e.cursor_position_set(*xy, move=True)

        def check_edit_text(expected):
            # Read the actual edit buffer, not just the workspace display property.
            clipboard = bpy.context.window_manager.clipboard
            try:
                bpy.context.window_manager.clipboard = "Workspace edit buffer not copied"
                yield e.ctrl.a().ctrl.c()
                t.assertEqual(bpy.context.window_manager.clipboard, expected)
            finally:
                bpy.context.window_manager.clipboard = clipboard

        yield from edit_tab()
        yield datetime.timedelta(seconds=0.2)
        _label_screenshot("tab-edit-open")
        expected = ws.display_name
        t.assertNotEqual(expected, ws.name)
        yield from check_edit_text(expected)
        # Confirming the translated text unchanged must preserve automatic translation.
        yield e.ret()
        t.assertEqual(ws.custom_display_name, "")
        view.language = 'en_US'
        t.assertEqual(ws.display_name, ws.name)
        view.language = 'vi_VN'
        t.assertEqual(ws.display_name, expected)
        # Typing immediately must append, without silently replacing the existing label.
        yield from edit_tab()
        yield e.text(" ")
        yield from check_edit_text(expected + " ")
        yield e.esc()
        t.assertEqual(ws.custom_display_name, "")
        yield from edit_tab()
        yield e.text(" Notes").ret()
        t.assertEqual(ws.custom_display_name, expected + " Notes")
        t.assertEqual(ws.name, "Layout")
        yield from edit_tab()
        yield e.ctrl.a().back_space().ret()
        t.assertEqual(ws.custom_display_name, "")
        yield from edit_tab()
        yield e.ctrl.a().text("Canceled label").esc()
        t.assertEqual(ws.custom_display_name, "")
        yield from edit_tab()
        yield e.ctrl.a().text("Custom tab label").ret()
        t.assertEqual(ws.custom_display_name, "Custom tab label")
        t.assertEqual((ws.name, ws.label_source), ("Layout", 'CANONICAL'))
        yield datetime.timedelta(seconds=0.1)
        _label_screenshot("edited-tab")
        yield from edit_tab()
        yield from check_edit_text("Custom tab label")
        yield e.ret()
        t.assertEqual(ws.custom_display_name, "Custom tab label")
        yield from edit_tab()
        yield e.text(" 2").ret()
        t.assertEqual(ws.custom_display_name, "Custom tab label 2")
        yield from edit_tab()
        yield e.back_space().ret()
        t.assertEqual(ws.custom_display_name, "Custom tab label ")
        yield from edit_tab()
        yield e.ctrl.a().back_space().ret()
        t.assertEqual(ws.custom_display_name, "")
        t.assertNotEqual(ws.display_name, ws.name)
    finally:
        bpy.types.CONSOLE_HT_header.remove(draw_tabs)
        ws.custom_display_name = ""
        view.language, view.use_translate_interface = previous
        area.type = old_type


def label_copy_and_append():
    import datetime
    from pathlib import Path
    import tempfile
    import bpy

    _e, t, window = ui.test_window()
    source = window.workspace
    base = source.name
    t.assertEqual(source.label_source, 'CANONICAL')
    source.custom_display_name = "Shared Label"
    original_pointer = source.as_pointer()

    def check_new(before):
        created = [ws for ws in bpy.data.workspaces if ws.as_pointer() not in before]
        t.assertEqual(len(created), 1)
        result = created[0]
        t.assertNotEqual(result.name, base)
        t.assertEqual((result.label_source, result.custom_display_name), ('LITERAL', "Shared Label"))
        t.assertEqual(result.display_mode, 'USE_USERDEFINED')
        t.assertEqual((source.name, source.label_source, source.as_pointer()),
                      (base, 'CANONICAL', original_pointer))
        t.assertEqual(source.custom_display_name, "Shared Label")
        t.assertEqual(window.workspace.as_pointer(), result.as_pointer())
        result.custom_display_name = ""
        t.assertEqual((result.display_mode, result.display_name), ('USE_DEFAULT', result.name))

    before = {ws.as_pointer() for ws in bpy.data.workspaces}
    t.assertEqual(bpy.ops.workspace.duplicate(), {'FINISHED'})
    yield datetime.timedelta(seconds=0.1)
    check_new(before)
    with tempfile.TemporaryDirectory(prefix="workspace-append-") as directory:
        library, current = (Path(directory) / name for name in ("library.blend", "current.blend"))
        for path in (library, current):
            t.assertEqual(bpy.ops.wm.save_as_mainfile(filepath=str(path), check_existing=False), {'FINISHED'})
        for path in (library, current):
            before = {ws.as_pointer() for ws in bpy.data.workspaces}
            t.assertEqual(bpy.ops.workspace.append_activate(idname=base, filepath=str(path)), {'FINISHED'})
            yield datetime.timedelta(seconds=0.1)
            check_new(before)


def sanity_check_general():
    e, t, window = ui.test_window()

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("ga")  # General > Animation
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Animation")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("gc")  # General > Compositing
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Compositing")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("gg")  # General > Geometry Nodes
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Geometry Nodes")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("gl")  # General > Layout
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Layout")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("gm")  # General > Modeling
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Modeling")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("gr")  # General > Rendering
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Rendering")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("gscr")  # General > Scripting
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Scripting")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("gscu")  # General > Sculpting
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Sculpting")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("gsh")  # General > Shading
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Shading")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("gt")  # General > Texture Paint
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Texture Paint")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("gu")  # General > UV Editing
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "UV Editing")


def sanity_check_2d_animation():
    e, t, window = ui.test_window()

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text(" 2d")  # 2D Animation > 2D Animation
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "2D Animation")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("fu")  # 2D Animation > 2D Full Canvas
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "2D Full Canvas")


def sanity_check_sculpting():
    e, t, window = ui.test_window()

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("sscu")  # Sculpting > Sculpting
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Sculpting")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("ssh")  # Sculpting > Shading
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Shading")


def sanity_check_storyboarding():
    e, t, window = ui.test_window()

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("sv")  # Storyboarding > Video Editing
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Video Editing")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("st")  # Storyboarding > Storyboarding
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Storyboarding")


def sanity_check_vfx():
    e, t, window = ui.test_window()

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("vc")  # VFX > Compositing
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Compositing")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("vma")  # VFX > Masking
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Masking")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("vmo")  # VFX > Motion Tracking
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Motion Tracking")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("vr")  # VFX > Rendering
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Rendering")


def sanity_check_video_editing():
    e, t, window = ui.test_window()

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("vir")  # Video Editing > Rendering
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Rendering")

    yield from ui.call_operator(e, "Add Workspace")
    yield e.text("vv")  # Video Editing > Video Editing
    yield e.ret()
    t.assertEqual(window.workspace.name_full.split(".", 1)[0], "Video Editing")
