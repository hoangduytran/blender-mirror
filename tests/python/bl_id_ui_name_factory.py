# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Check saved marks and translator extraction in approved bundled assets."""

import importlib.util
import json
from pathlib import Path
import unittest

import bpy
from _bl_i18n_utils import bl_extract_messages, settings


ROOT = Path(__file__).resolve().parents[2]


class FactoryUINameTest(unittest.TestCase):
    """Check actual factory files without writing their contents."""

    def test_saved_factory_asset_notes_and_source_names(self):
        manifest = ROOT / "tools/utils/blend_ui_name_factory_files.json"
        totals = {"Brush": 0, "NodeTree": 0}
        for filename in json.loads(manifest.read_text()):
            bpy.ops.wm.open_mainfile(filepath=str(ROOT / filename))
            local_assets = [item for item in bpy.data.user_map()
                            if item.library is None and item.asset_data is not None]
            self.assertTrue(local_assets, filename)
            for item in local_assets:
                with self.subTest(file=filename, name=item.name):
                    self.assertTrue(item.ui_name_is_translatable)
                    self.assertEqual(item.asset_data["_blender_ui_name"]["source"], item.name)
                    context = item.ui_name_translation_context
                    totals[context] = totals.get(context, 0) + 1
        self.assertGreater(totals["Brush"], 0)
        self.assertGreater(totals["NodeTree"], 0)

    def test_extraction_uses_saved_permission_and_id_context(self):
        messages = []
        original = bl_extract_messages.process_msg
        def collect(msgs, context, name, source, reports, checks, config):
            messages.append((context, name, source))
        try:
            bl_extract_messages.process_msg = collect
            bl_extract_messages.dump_asset_messages({}, {}, settings)
        finally:
            bl_extract_messages.process_msg = original
        contexts = {context for context, _, source in messages if source.startswith("Asset name")}
        self.assertIn("Brush", contexts)
        self.assertIn("NodeTree", contexts)

    def test_authoring_refuses_unapproved_user_files(self):
        spec = importlib.util.spec_from_file_location(
            "factory_name_author", ROOT / "tools/utils/blend_author_ui_names.py")
        author = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(author)
        with self.assertRaises(ValueError):
            author.author_file(ROOT / "tests/files/user-created.blend", True)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        personal = bpy.data.objects.new("Personal Asset", None)
        personal.asset_mark()
        approved_file = ROOT / json.loads(author.MANIFEST.read_text())[0]
        with self.assertRaises(ValueError):
            author.author_file(approved_file, False)


is_main_module = __name__ == "__main__"
if is_main_module:
    unittest.main(argv=[__file__])
