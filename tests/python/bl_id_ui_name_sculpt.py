# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Check the installed factory brush in actual Sculpt Mode, without screen claims."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import bpy


class FactorySculptUINameTest(unittest.TestCase):
    def test_factory_selection_locale_copy_and_reopen(self):
        view = bpy.context.preferences.view
        original_preferences = (view.language, view.use_translate_interface,
                                view.use_translate_new_dataname)
        try:
            view.language = 'vi_VN'
            view.use_translate_interface = True
            view.use_translate_new_dataname = True
            translated = bpy.app.translations.pgettext_iface("Smooth", "Brush")
            self.assertNotEqual(translated, "Smooth", "Installed Vietnamese Brush catalog is missing")
            self.assertEqual(bpy.ops.object.mode_set(mode='SCULPT'), {'FINISHED'})
            self.assertEqual(bpy.context.mode, 'SCULPT')
            self.assertEqual(bpy.ops.brush.asset_activate(
                asset_library_type='ESSENTIALS',
                relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth'),
                {'FINISHED'})
            brush = bpy.context.tool_settings.sculpt.brush
            self.assertEqual(brush.name, "Smooth")
            self.assertTrue(brush.ui_name_is_translatable)
            self.assertEqual(brush.ui_name, translated)
            view.use_translate_interface = False
            self.assertEqual(brush.ui_name, "Smooth")
            self.assertTrue(brush.ui_name_is_translatable)
            view.language = 'en_US'
            view.use_translate_interface = True
            self.assertEqual(brush.ui_name, "Smooth")
            view.language = 'vi_VN'
            self.assertEqual(brush.ui_name, translated)
            self.assertEqual(brush.name, "Smooth")

            with TemporaryDirectory(prefix="ui_name_sculpt_") as directory:
                filepath = str(Path(directory) / "sculpt.blend")
                bpy.ops.wm.save_as_mainfile(filepath=filepath)
                bpy.ops.wm.open_mainfile(filepath=filepath, load_ui=False)
                self.assertEqual(bpy.context.mode, 'SCULPT')
                self.assertEqual(bpy.ops.brush.asset_activate(
                    asset_library_type='ESSENTIALS',
                    relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth'),
                    {'FINISHED'})
                restored = bpy.context.tool_settings.sculpt.brush
                self.assertEqual(restored.name, "Smooth")
                self.assertTrue(restored.ui_name_is_translatable)
                self.assertEqual(restored.ui_name, translated)
                self.assertEqual(bpy.ops.brush.asset_save_as(
                    name="My Favourite Smooth", asset_library_reference="LOCAL", catalog_path=""),
                    {'FINISHED'})
                personal = bpy.context.tool_settings.sculpt.brush
                self.assertEqual(personal.name, "My Favourite Smooth")
                self.assertFalse(personal.ui_name_is_translatable)
                self.assertEqual(personal.ui_name, personal.name)
                personal.name = "Smooth"
                self.assertFalse(personal.ui_name_is_translatable)
                self.assertEqual(personal.ui_name, personal.name)
                bpy.ops.wm.save_as_mainfile(filepath=filepath)
                bpy.ops.wm.open_mainfile(filepath=filepath, load_ui=False)
                local_brushes = [item for item in bpy.data.brushes if item.library is None]
                self.assertTrue(local_brushes)
                for item in local_brushes:
                    self.assertFalse(item.ui_name_is_translatable)
                    self.assertEqual(item.ui_name, item.name)
        finally:
            view.language, view.use_translate_interface, view.use_translate_new_dataname = original_preferences


def main():
    has_arguments = "--" in sys.argv
    arguments = sys.argv[sys.argv.index("--") + 1:] if has_arguments else []
    unittest.main(argv=[__file__, *arguments])


is_main_module = __name__ == "__main__"
if is_main_module:
    main()
