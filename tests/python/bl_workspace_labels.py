# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Workspace label API and persistence tests; translation is tested in ui_simulate."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import bpy


def saved_state():
    return {ws.name: (ws.label_source, ws.custom_display_name) for ws in bpy.data.workspaces}


def window_workspaces():
    return [(window.workspace.name, window.screen.name) for window in bpy.context.window_manager.windows]


class WorkspaceLabelTest(unittest.TestCase):
    def setUp(self):
        # Unlike read_homefile(factory), this also resets a previous Load UI override.
        bpy.ops.wm.read_factory_settings(use_empty=False)
        prefs = bpy.context.preferences
        prefs.use_preferences_save = False
        prefs.filepaths.file_preview_type = 'NONE'
        prefs.filepaths.save_version = 0
        prefs.view.language = 'en_US'
        prefs.view.use_translate_interface = False
        self.temp = tempfile.TemporaryDirectory(prefix="workspace-labels-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "labels.blend"
        ws = bpy.data.workspaces["Layout"]
        self.assertEqual((ws.label_source, ws.custom_display_name), ('CANONICAL', ""))

    def save(self):
        self.assertEqual(bpy.ops.wm.save_as_mainfile(
            filepath=str(self.path), check_existing=False, compress=False), {'FINISHED'})

    def test_custom_reset_and_identity(self):
        ws = bpy.data.workspaces["Layout"]
        original = ws.as_pointer()
        for label in ("My Workspace", "B\u1ed1 c\u1ee5c c\u1ee7a t\u00f4i", "  ", ws.name):
            with self.subTest(label=label):
                ws.custom_display_name = label
                self.assertEqual(ws.display_name, label)
                self.assertEqual(ws.display_mode, 'USE_USERDEFINED')
                self.assertEqual((ws.name, ws.label_source, ws.as_pointer()),
                                 ("Layout", 'CANONICAL', original))
        ws.custom_display_name = ""
        # Setup disables translation; the UI suite covers the translated mode.
        self.assertEqual(ws.display_mode, 'USE_DEFAULT')
        self.assertEqual(ws.display_name, "Layout")

    def test_name_and_derived_properties_readonly(self):
        ws = bpy.data.workspaces["Layout"]
        before = saved_state()
        with self.assertRaises(AttributeError):
            ws.name = "Changed"
        for mode in ('NEVER', 'ALWAYS', 'SAME_ROOT'):
            with self.subTest(mode=mode):
                with self.assertRaisesRegex(RuntimeError, "read-only"):
                    ws.rename("Modeling", mode=mode)
                self.assertEqual(saved_state(), before)
        for name, value in (("label_source", 'LITERAL'), ("display_mode", 'USE_DEFAULT'),
                            ("display_name", "Changed")):
            with self.subTest(property=name):
                self.assertTrue(ws.is_property_readonly(name))
                with self.assertRaises(AttributeError):
                    setattr(ws, name, value)
        self.assertFalse(ws.is_property_readonly("custom_display_name"))

    def test_identical_custom_labels(self):
        first, second = bpy.data.workspaces["Layout"], bpy.data.workspaces["Modeling"]
        first.custom_display_name = second.custom_display_name = "Shared"
        self.assertEqual(first.display_name, second.display_name)
        self.assertNotEqual(first.as_pointer(), second.as_pointer())
        self.assertEqual((first.name, second.name), ("Layout", "Modeling"))

    def test_utf8_capacity_and_self_assignment(self):
        ws = bpy.data.workspaces["Layout"]
        ws.custom_display_name = "\u00e9" * 300
        label = ws.custom_display_name
        self.assertTrue(label)
        self.assertLessEqual(len(label.encode("utf-8")), 255)
        self.assertEqual(label.encode("utf-8").decode("utf-8"), label)
        ws.custom_display_name = ws.custom_display_name
        self.assertEqual(ws.custom_display_name, label)
        self.assertEqual((ws.name, ws.label_source), ("Layout", 'CANONICAL'))

    def test_other_ids_still_rename(self):
        obj = bpy.data.objects.new("Label Test", None)
        obj.name = "Renamed"
        self.assertEqual(obj.name, "Renamed")
        obj.rename("Renamed Again")
        self.assertEqual(obj.name, "Renamed Again")

    def test_save_reload_with_ui(self):
        # Unicode storage is independent of the operating system's input method.
        bpy.data.workspaces["Layout"].custom_display_name = "B\u1ed1 Tr\u00ed M\u1edbi"
        expected, active = saved_state(), window_workspaces()
        self.save()
        bpy.data.workspaces["Layout"].custom_display_name = "Unsaved"
        self.assertEqual(bpy.ops.wm.open_mainfile(filepath=str(self.path), load_ui=True), {'FINISHED'})
        self.assertEqual(saved_state(), expected)
        self.assertEqual(window_workspaces(), active)

    def test_load_without_ui_keeps_session_labels(self):
        bpy.data.workspaces["Layout"].custom_display_name = "Saved Label"
        self.save()
        bpy.data.workspaces["Layout"].custom_display_name = "Session Label"
        bpy.context.window.workspace = bpy.data.workspaces["Modeling"]
        expected, active = saved_state(), window_workspaces()
        self.assertEqual(bpy.ops.wm.open_mainfile(filepath=str(self.path), load_ui=False), {'FINISHED'})
        self.assertEqual(saved_state(), expected)
        self.assertEqual(window_workspaces(), active)

    def test_isolated_user_startup(self):
        # Use separate processes and an existing config directory, never the user's startup.
        config = Path(self.temp.name) / "config"
        config.mkdir()
        env = dict(os.environ, BLENDER_USER_CONFIG=str(config),
                   BLENDER_USER_EXTENSIONS=str(Path(self.temp.name) / "extensions"))
        for action in ("save", "load"):
            command = [bpy.app.binary_path, "--background", "--factory-startup", "--disable-autoexec",
                       "--python-exit-code", "1", "--python", str(Path(__file__).resolve()),
                       "--", "--startup-worker", action]
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((config / "startup.blend").is_file())

    def test_legacy_files_and_resave(self):
        fixture_dir = Path(__file__).resolve().parents[1] / "files" / "workspace_labels"
        manifest = json.loads((fixture_dir / "legacy.json").read_text(encoding="utf-8"))
        for fixture in manifest["fixtures"]:
            with self.subTest(fixture=fixture["path"]):
                self.assertEqual(bpy.ops.wm.open_mainfile(
                    filepath=str(fixture_dir / fixture["path"]), load_ui=True), {'FINISHED'})
                self.assertEqual(sorted(bpy.data.workspaces.keys()), sorted(fixture["workspace_names"]))
                for ws in bpy.data.workspaces:
                    self.assertEqual((ws.label_source, ws.custom_display_name), ('LITERAL', ""))
                    self.assertEqual(ws.display_name, ws.name)
                    ws.custom_display_name = "Temporary"
                    ws.custom_display_name = ""
                    self.assertEqual(ws.display_name, ws.name)
                bpy.data.workspaces[0].custom_display_name = "Saved legacy override"
                expected = saved_state()
                self.save()
                bpy.ops.wm.open_mainfile(filepath=str(self.path), load_ui=True)
                self.assertEqual(saved_state(), expected)


def startup_worker(action):
    config = Path(os.environ["BLENDER_USER_CONFIG"]).resolve()
    assert Path(bpy.utils.user_resource('CONFIG')).resolve() == config
    prefs = bpy.context.preferences
    prefs.use_preferences_save = False
    prefs.filepaths.file_preview_type = 'NONE'
    prefs.filepaths.save_version = 0
    is_save = action == "save"
    if is_save:
        bpy.data.workspaces["Layout"].custom_display_name = "Startup Label"
        assert bpy.ops.wm.save_homefile() == {'FINISHED'}
        bpy.data.workspaces["Layout"].custom_display_name = "Unsaved Project Label"
    assert bpy.ops.wm.read_homefile(use_factory_startup=False) == {'FINISHED'}
    ws = bpy.data.workspaces["Layout"]
    assert (ws.label_source, ws.custom_display_name) == ('CANONICAL', "Startup Label")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--startup-worker", choices=("save", "load"))
    options, remaining = parser.parse_known_args(args)
    is_worker = options.startup_worker is not None
    if is_worker:
        startup_worker(options.startup_worker)
    else:
        unittest.main(argv=[sys.argv[0], *remaining])
