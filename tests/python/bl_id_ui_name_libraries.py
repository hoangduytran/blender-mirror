# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Check display-name ownership using real linked, appended and overridden objects."""

import hashlib
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import bpy


class IDUINameLibraryTest(unittest.TestCase):
    def setUp(self):
        author_method = bpy.types.ID.bl_rna.functions.get("ui_name_translation_mark")
        self.assertIsNotNone(author_method, "This Blender build lacks ID.ui_name_translation_mark")
        self.directory = TemporaryDirectory(prefix="ui_name_library_")
        self.library_path = Path(self.directory.name) / "source.blend"
        self.source_name = "UI Name Linked Object Test"
        item = bpy.data.objects.new(self.source_name, None)
        item.ui_name_translation_mark()
        item.asset_mark()
        item.asset_data.author = "Library test author"
        unmarked = bpy.data.objects.new("Layout", None)
        bpy.data.libraries.write(str(self.library_path), {item, unmarked}, fake_user=True)
        bpy.data.batch_remove(ids=(item, unmarked))
        self.source_digest = hashlib.sha256(self.library_path.read_bytes()).digest()
        self.original_language = bpy.context.preferences.view.language
        self.original_translate = bpy.context.preferences.view.use_translate_interface
        self.module = "blender_ui_name_library_test"
        bpy.app.translations.register(self.module, {
            "vi_VN": {("Object", self.source_name): "Vật thể liên kết thử nghiệm"},
        })
        bpy.context.preferences.view.language = 'vi_VN'
        bpy.context.preferences.view.use_translate_interface = True
        self.created_names = {self.source_name, "Layout"}

    def tearDown(self):
        bpy.app.translations.unregister(self.module)
        bpy.context.preferences.view.language = self.original_language
        bpy.context.preferences.view.use_translate_interface = self.original_translate
        remove = []
        for item in bpy.data.objects:
            is_test_item = item.name in self.created_names or item.name.startswith(self.source_name + ".")
            if is_test_item:
                remove.append(item)
        bpy.data.batch_remove(ids=remove)
        self.assertEqual(hashlib.sha256(self.library_path.read_bytes()).digest(), self.source_digest)
        self.directory.cleanup()

    def load_object(self, name=None, link=False):
        requested_name = self.source_name if name is None else name
        with bpy.data.libraries.load(str(self.library_path), link=link) as (_, data_to):
            data_to.objects = [requested_name]
        item = data_to.objects[0]
        self.assertIsNotNone(item)
        self.created_names.add(item.name)
        return item

    def reopen(self):
        filepath = str(Path(self.directory.name) / "roundtrip.blend")
        bpy.ops.wm.save_as_mainfile(filepath=filepath)
        bpy.ops.wm.open_mainfile(filepath=filepath, load_ui=False)

    def find_restored(self, linked=False, overridden=False):
        matches = []
        for item in bpy.data.objects:
            has_requested_ownership = item.name == self.source_name and (
                (linked and item.library is not None) or
                (overridden and item.override_library is not None))
            if has_requested_ownership:
                matches.append(item)
        self.assertEqual(len(matches), 1)
        return matches[0]

    def test_linked_source_stays_owned_and_translates_without_writing_library(self):
        item = self.load_object(link=True)
        self.assertIsNotNone(item.library)
        self.assertTrue(item.ui_name_is_translatable)
        self.assertEqual(item.name, self.source_name)
        self.assertEqual(item.ui_name, "Vật thể liên kết thử nghiệm")
        with self.assertRaises(RuntimeError):
            item.ui_name_translation_mark()
        with self.assertRaises(RuntimeError):
            item.ui_name_translation_clear()
        bpy.context.scene.collection.objects.link(item)
        self.reopen()
        restored = self.find_restored(linked=True)
        self.assertTrue(restored.ui_name_is_translatable)
        self.assertEqual(restored.ui_name, "Vật thể liên kết thử nghiệm")
        self.assertEqual(restored.asset_data.author, "Library test author")

    def test_append_keeps_note_until_collision_or_user_rename(self):
        item = self.load_object()
        self.assertIsNone(item.library)
        self.assertTrue(item.ui_name_is_translatable)
        self.assertEqual(item.ui_name, "Vật thể liên kết thử nghiệm")
        collision = self.load_object()
        self.assertEqual(collision.name, self.source_name + ".001")
        self.assertFalse(collision.ui_name_is_translatable)
        self.assertTrue(item.ui_name_is_translatable)
        item.name = "Personal appended object"
        self.created_names.add(item.name)
        self.assertFalse(item.ui_name_is_translatable)
        item.name = self.source_name
        self.assertFalse(item.ui_name_is_translatable)
        bpy.context.scene.collection.objects.link(item)
        bpy.context.scene.collection.objects.link(collision)
        self.reopen()
        self.assertFalse(bpy.data.objects[self.source_name].ui_name_is_translatable)
        self.assertFalse(bpy.data.objects[self.source_name + ".001"].ui_name_is_translatable)

    def test_override_keeps_unchanged_name_then_rename_roundtrip_stays_literal(self):
        linked = self.load_object(link=True)
        # Instantiating the linked object makes it a direct library user, as in normal linking.
        bpy.context.scene.collection.objects.link(linked)
        local = linked.override_create()
        self.assertIsNotNone(local)
        self.assertIsNotNone(local.override_library)
        self.assertIsNone(local.library)
        self.assertEqual(local.name, self.source_name)
        self.assertTrue(local.ui_name_is_translatable)
        self.assertEqual(local.ui_name, "Vật thể liên kết thử nghiệm")
        bpy.context.scene.collection.objects.link(local)
        self.reopen()
        local = self.find_restored(overridden=True)
        self.assertTrue(local.ui_name_is_translatable)
        self.assertEqual(local.ui_name, "Vật thể liên kết thử nghiệm")
        local.name = "Personal overridden object"
        self.created_names.add(local.name)
        self.assertFalse(local.ui_name_is_translatable)
        local.name = self.source_name
        self.assertFalse(local.ui_name_is_translatable)
        self.reopen()
        local = self.find_restored(overridden=True)
        self.assertFalse(local.ui_name_is_translatable)
        self.assertEqual(local.ui_name, self.source_name)
        self.assertTrue(local.override_library.reference.ui_name_is_translatable)

    def test_unmarked_library_name_is_not_guessed(self):
        item = self.load_object(name="Layout")
        self.assertFalse(item.ui_name_is_translatable)
        self.assertEqual(item.ui_name, "Layout")
        bpy.context.scene.collection.objects.link(item)
        self.reopen()
        self.assertFalse(bpy.data.objects["Layout"].ui_name_is_translatable)


def main():
    has_script_arguments = "--" in sys.argv
    arguments = sys.argv[sys.argv.index("--") + 1:] if has_script_arguments else []
    unittest.main(argv=[__file__, *arguments])


is_main_module = __name__ == "__main__"
if is_main_module:
    main()
