# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Check marked display names through Blender's real Python interface."""

import pathlib
import sys
import tempfile
import unittest

import bpy


class IDUINameTest(unittest.TestCase):
    def setUp(self):
        # Fail clearly on an old build before calling the missing feature.
        author_method = bpy.types.ID.bl_rna.functions.get("ui_name_translation_mark")
        self.assertIsNotNone(author_method, "This Blender build lacks ID.ui_name_translation_mark")
        self.object_names = []
        self.brush_names = []
        self.node_names = []
        self.original_language = bpy.context.preferences.view.language
        self.original_translate = bpy.context.preferences.view.use_translate_interface
        self.original_translate_new = bpy.context.preferences.view.use_translate_new_dataname
        bpy.context.preferences.view.use_translate_interface = False

    def tearDown(self):
        for names, collection in (
                (self.object_names, bpy.data.objects),
                (self.brush_names, bpy.data.brushes),
                (self.node_names, bpy.data.node_groups)):
            for name in names:
                item = collection.get(name)
                has_item = item is not None
                if has_item:
                    collection.remove(item, do_unlink=True)
        bpy.context.preferences.view.language = self.original_language
        bpy.context.preferences.view.use_translate_interface = self.original_translate
        bpy.context.preferences.view.use_translate_new_dataname = self.original_translate_new

    def new_object(self, name="UI Name Test"):
        item = bpy.data.objects.new(name, None)
        self.object_names.append(item.name)
        return item

    def test_name_stays_writable_and_unmarked(self):
        item = self.new_object("Layout")
        self.assertFalse(item.ui_name_is_translatable)
        self.assertEqual(item.ui_name, item.name)
        item.name = "Personal workspace"
        self.object_names.append(item.name)
        self.assertEqual(item.ui_name, "Personal workspace")

    def test_mark_clear_and_readonly_display_properties(self):
        item = self.new_object()
        item.ui_name_translation_mark()
        self.assertTrue(item.ui_name_is_translatable)
        self.assertEqual(item.ui_name, item.name)
        with self.assertRaises(AttributeError):
            item.ui_name = "Replacement"
        with self.assertRaises(AttributeError):
            item.ui_name_is_translatable = False
        self.assertEqual(item.ui_name_translation_context, bpy.app.translations.contexts.id_object)
        with self.assertRaises(AttributeError):
            item.ui_name_translation_context = "Replacement"
        item.ui_name_translation_clear()
        self.assertFalse(item.ui_name_is_translatable)

    def test_unchanged_name_keeps_mark_but_rename_back_does_not(self):
        item = self.new_object()
        original = item.name
        item.ui_name_translation_mark()
        item.name = original
        self.assertTrue(item.ui_name_is_translatable)
        item.name = "Personal name"
        self.object_names.append(item.name)
        self.assertFalse(item.ui_name_is_translatable)
        item.name = original
        self.assertFalse(item.ui_name_is_translatable)

    def test_user_copy_is_literal(self):
        item = self.new_object()
        item.ui_name_translation_mark()
        copied = item.copy()
        self.object_names.append(copied.name)
        self.assertTrue(item.ui_name_is_translatable)
        self.assertFalse(copied.ui_name_is_translatable)
        self.assertEqual(copied.ui_name, copied.name)

    def test_brush_and_node_group_use_shared_rule(self):
        brush = bpy.data.brushes.new("UI Name Brush", mode='SCULPT')
        node = bpy.data.node_groups.new("UI Name Node Tool", 'GeometryNodeTree')
        self.brush_names.append(brush.name)
        self.node_names.append(node.name)
        self.assertEqual(brush.ui_name_translation_context, bpy.app.translations.contexts.id_brush)
        self.assertEqual(node.ui_name_translation_context, bpy.app.translations.contexts.id_nodetree)
        for item in (brush, node):
            item.ui_name_translation_mark()
            self.assertTrue(item.ui_name_is_translatable)
            item.name += " Personal"
            self.assertFalse(item.ui_name_is_translatable)
        self.brush_names.append(brush.name)
        self.node_names.append(node.name)

    def test_four_types_share_locale_fallback_and_collision_rules(self):
        view = bpy.context.preferences.view
        supports_vietnamese = "vi_VN" in view.bl_rna.properties["language"].enum_items
        if not supports_vietnamese:
            self.skipTest("Build does not provide Vietnamese interface translation")
        cases = (
            (bpy.data.materials, lambda name: bpy.data.materials.new(name), "Material"),
            (bpy.data.objects, lambda name: bpy.data.objects.new(name, None), "Object"),
            (bpy.data.collections, lambda name: bpy.data.collections.new(name), "Collection"),
            (bpy.data.actions, lambda name: bpy.data.actions.new(name), "Action"),
        )
        items = []
        module = "blender_ui_name_four_types_test"
        catalog = {}
        for _, create, context in cases:
            item = create("UI name locale test " + context)
            missing = create("UI name missing catalog " + context)
            item.ui_name_translation_mark()
            missing.ui_name_translation_mark()
            items.extend((item, missing))
            catalog[(context, item.name)] = "Tên mẫu " + context
        bpy.app.translations.register(module, {"vi_VN": catalog})
        try:
            for index, (collection, _, context) in enumerate(cases):
                item, missing = items[index * 2:index * 2 + 2]
                source = item.name
                self.assertEqual(item.ui_name_translation_context, context)
                translated = catalog[(context, source)]
                view.language = 'vi_VN'
                view.use_translate_interface = True
                self.assertEqual(item.ui_name, translated)
                self.assertEqual(item.name, source)
                self.assertEqual(missing.ui_name, missing.name)
                self.assertTrue(missing.ui_name_is_translatable)
                view.use_translate_interface = False
                self.assertEqual(item.ui_name, source)
                self.assertTrue(item.ui_name_is_translatable)
                view.language = 'en_US'
                view.use_translate_interface = True
                self.assertEqual(item.ui_name, source)
                view.language = 'vi_VN'
                self.assertEqual(item.ui_name, translated)
                duplicate = item.copy()
                items.append(duplicate)
                self.assertEqual(duplicate.name, source + ".001")
                self.assertFalse(duplicate.ui_name_is_translatable)
                self.assertEqual(duplicate.ui_name, duplicate.name)
                self.assertTrue(item.ui_name_is_translatable)
                self.assertIs(collection[source], item)
                item.name = "Personal " + context
                self.assertFalse(item.ui_name_is_translatable)
                item.name = source
                self.assertFalse(item.ui_name_is_translatable)
                self.assertEqual(item.ui_name, source)
        finally:
            bpy.app.translations.unregister(module)
            bpy.data.batch_remove(ids=items)

    def test_factory_workspaces_marked_but_same_spelling_user_data_literal(self):
        self.assertGreater(len(bpy.data.workspaces), 0)
        for workspace in bpy.data.workspaces:
            self.assertTrue(workspace.ui_name_is_translatable, msg=workspace.name)
            item = self.new_object(workspace.name)
            self.assertFalse(item.ui_name_is_translatable)
            self.assertEqual(item.ui_name, item.name)

    def test_save_reopen_keeps_mark_and_source_name(self):
        item = self.new_object()
        item.use_fake_user = True
        item.ui_name_translation_mark()
        original = item.name
        with tempfile.TemporaryDirectory(prefix="blender_ui_name_") as directory:
            filepath = str(pathlib.Path(directory) / "marked.blend")
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
            bpy.ops.wm.open_mainfile(filepath=filepath, load_ui=False)
            restored = bpy.data.objects.get(original)
            self.assertIsNotNone(restored)
            self.assertEqual(restored.name, original)
            self.assertTrue(restored.ui_name_is_translatable)
            self.assertEqual(restored.ui_name, original)

    def test_injected_workspace_translation_changes_only_display(self):
        view = bpy.context.preferences.view
        language_items = view.bl_rna.properties["language"].enum_items
        supports_vietnamese = "vi_VN" in language_items
        if not supports_vietnamese:
            self.skipTest("Build does not provide Vietnamese interface translation")
        workspace = bpy.context.workspace
        original_name = workspace.name
        originally_marked = workspace.ui_name_is_translatable
        source_name = "UI Name Injected Translation Test"
        workspace.name = source_name
        # ID display names use the ID type's category, rather than the RNA struct's category.
        context = "WorkSpace"
        module = "blender_id_ui_name_test"
        bpy.app.translations.register(module, {"vi_VN": {(context, source_name): "Tên thử nghiệm"}})
        try:
            workspace.ui_name_translation_mark()
            view.language = 'vi_VN'
            view.use_translate_interface = True
            self.assertEqual(workspace.ui_name, "Tên thử nghiệm")
            self.assertEqual(workspace.name, source_name)
            view.use_translate_interface = False
            self.assertEqual(workspace.ui_name, source_name)
        finally:
            bpy.app.translations.unregister(module)
            should_clear = not originally_marked
            if should_clear:
                workspace.ui_name_translation_clear()
            workspace.name = original_name
            if originally_marked:
                workspace.ui_name_translation_mark()

    def test_workspace_append_keeps_source_and_makes_collision_literal(self):
        view = bpy.context.preferences.view
        supports_vietnamese = "vi_VN" in view.bl_rna.properties["language"].enum_items
        if not supports_vietnamese:
            self.skipTest("Build does not provide Vietnamese interface translation")
        workspace = bpy.context.workspace
        original_name = workspace.name
        originally_marked = workspace.ui_name_is_translatable
        module = "blender_workspace_append_ui_name_test"
        source_name = "UI Name Workspace Append"
        workspace.name = source_name
        workspace.ui_name_translation_mark()
        existing_pointers = {item.as_pointer() for item in bpy.data.workspaces}
        bpy.app.translations.register(module, {"vi_VN": {("WorkSpace", source_name): "Không đổi tên"}})
        try:
            with tempfile.TemporaryDirectory(prefix="blender_workspace_append_") as directory:
                filepath = str(pathlib.Path(directory) / "workspace.blend")
                # Saving a copy keeps the current project separate from the append source.
                bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)
                view.language = 'vi_VN'
                view.use_translate_interface = True
                view.use_translate_new_dataname = True
                result = bpy.ops.workspace.append_activate(filepath=filepath, idname=source_name)
                self.assertEqual(result, {'FINISHED'})
                appended = []
                for item in bpy.data.workspaces:
                    is_appended_workspace = item.as_pointer() not in existing_pointers
                    if is_appended_workspace:
                        appended.append(item)
                self.assertEqual(len(appended), 1)
                self.assertEqual(appended[0].name, source_name + ".001")
                self.assertFalse(appended[0].ui_name_is_translatable)
                self.assertEqual(appended[0].ui_name, appended[0].name)
                self.assertEqual(workspace.name, source_name)
                self.assertTrue(workspace.ui_name_is_translatable)
                self.assertEqual(workspace.ui_name, "Không đổi tên")
        finally:
            bpy.app.translations.unregister(module)
            for item in list(bpy.data.workspaces):
                is_appended_workspace = item.as_pointer() not in existing_pointers
                if is_appended_workspace:
                    bpy.data.batch_remove(ids=(item,))
            workspace.name = original_name
            if originally_marked:
                workspace.ui_name_translation_mark()


def main():
    has_script_arguments = "--" in sys.argv
    test_arguments = sys.argv[sys.argv.index("--") + 1:] if has_script_arguments else []
    unittest.main(argv=[__file__, *test_arguments])


is_main_module = __name__ == "__main__"
if is_main_module:
    main()
