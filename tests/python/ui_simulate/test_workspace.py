# SPDX-FileCopyrightText: 2025 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
This file does not run anything, its methods are accessed for tests by ``run_blender_setup.py``.
"""
import modules.ui_test_utils as ui


def ui_name_editing_space_appends():
    # bpy is available only in Blender, whereas the host runner imports this file to list tests.
    import datetime
    import bpy

    e, t, window = ui.test_window()
    manager = bpy.context.window_manager
    workspace = window.workspace
    area = ui.get_window_area_by_type(window, 'VIEW_3D')
    old_type = area.type
    view = bpy.context.preferences.view
    previous = (view.language, view.use_translate_interface)
    original = workspace.name
    was_marked = workspace.ui_name_is_translatable
    clipboard = manager.clipboard
    draw_tab = False
    translation_module = "blender_ui_name_input_test"
    long_source = "Review Name Capacity"
    long_display = "Bố Trí " * 80
    translation_registered = False

    def draw_name(self, context):
        if draw_tab:
            self.layout.template_ID_tabs(context.window, "workspace")
        else:
            self.layout.prop(context.window.workspace, "name", text="")

    bpy.types.CONSOLE_HT_header.append(draw_name)
    try:
        area.type = 'CONSOLE'
        view.language = 'vi_VN'
        view.use_translate_interface = True
        bpy.app.translations.register(translation_module, {
            'vi_VN': {(workspace.ui_name_translation_context, long_source): long_display},
        })
        translation_registered = True
        cases = (
            ("Bố Trí kiểm tra", False, 'vi_VN', True),
            (original, False, 'vi_VN', True),
            (original, True, 'vi_VN', False),
            (original, True, 'en_US', True),
            ("Review Untranslated", True, 'vi_VN', True),
            (original, True, 'vi_VN', True),
            (long_source, True, 'vi_VN', True),
        )
        for source, marked, language, interface in cases:
            workspace.name = source
            if marked:
                workspace.ui_name_translation_mark()
            else:
                workspace.ui_name_translation_clear()
            view.language = language
            view.use_translate_interface = interface
            display = workspace.ui_name
            expects_translation = marked and interface and language == 'vi_VN' and source in (original, long_source)
            if expects_translation:
                t.assertNotEqual(display, source, "A distinct Vietnamese translation is required")
            else:
                t.assertEqual(display, source)
            is_long_translation = source == long_source
            if is_long_translation:
                t.assertEqual(display, long_display)
                t.assertGreater(len(display.encode('utf-8')), 255)
            for draw_tab in (True, False):
                # The draw callback changes with this case; explicitly rebuild its header.
                area.tag_redraw()
                yield e.cursor_position_set(100, 100, move=True)
                yield datetime.timedelta(seconds=0.2)
                region = next(region for region in area.regions if region.type == 'HEADER')
                data = window if draw_tab else workspace
                prop = "workspace" if draw_tab else "name"
                with bpy.context.temp_override(window=window, area=area, region=region):
                    xy = manager.try_activate_rna_button(region, data, prop, 'TEXT_EDITING')
                t.assertTrue(xy, (source, marked, language, interface, prop))
                yield e.cursor_position_set(*xy, move=True)
                # Reuse the previous fix's first-key check before selecting any text.
                yield e.text(" ").ctrl.a().ctrl.c()
                t.assertEqual(manager.clipboard, display + " ", "Workspace tab" if draw_tab else "Workspace name field")
                # Collapse the explicit copy selection and append a real UTF8 character.
                yield e.right_arrow().text_unicode("Đ").ctrl.a().ctrl.c()
                t.assertEqual(manager.clipboard, display + " Đ")
                yield e.esc()
                t.assertEqual(workspace.name, source)
                t.assertEqual(workspace.ui_name_is_translatable, marked)
                area.tag_redraw()
                yield datetime.timedelta(seconds=0.2)
                with bpy.context.temp_override(window=window, area=area, region=region):
                    xy = manager.try_activate_rna_button(region, data, prop, 'TEXT_EDITING')
                t.assertTrue(xy, (source, marked, language, interface, prop, "reopen"))
                yield e.cursor_position_set(*xy, move=True)
                yield e.ret()
                t.assertEqual(workspace.name, source)
                t.assertEqual(workspace.ui_name_is_translatable, marked)
    finally:
        bpy.types.CONSOLE_HT_header.remove(draw_name)
        if translation_registered:
            bpy.app.translations.unregister(translation_module)
        manager.clipboard = clipboard
        workspace.name = original
        if was_marked:
            workspace.ui_name_translation_mark()
        else:
            workspace.ui_name_translation_clear()
        view.language, view.use_translate_interface = previous
        area.type = old_type


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
