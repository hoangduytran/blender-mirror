"""Check the proposed rules in a small example, not in Blender or its screens."""

from copy import deepcopy
import unittest

from name_localization import (
    DataName, ExternalAsset, KEY, eligible, presentation_order, search,
)


CATALOG = {
    ("vi", "WorkSpace", "Layout"): "Bố Trí",
    ("vi", "Brush", "Draw"): "Vẽ",
    ("vi", "NodeTree", "Scatter"): "Rải",
    ("vi", "Brush", "Layout"): "Bố Cục Cọ",
    ("vi", "WorkSpace", "Second"): "Bố Trí",
}


def marked(name="Layout", kind="WORKSPACE", identity="local:1", asset=True):
    data = DataName(identity, kind, name, asset_properties={} if asset else None)
    data.mark()
    return data


class NameLocalizationTests(unittest.TestCase):
    def test_runtime_language_across_three_types(self):
        for kind, source, expected in (
            ("WORKSPACE", "Layout", "Bố Trí"),
            ("BRUSH", "Draw", "Vẽ"),
            ("NODETREE", "Scatter", "Rải"),
        ):
            with self.subTest(kind=kind):
                data = marked(source, kind)
                saved = data.save()
                self.assertEqual(data.display("vi", CATALOG), expected)
                self.assertEqual(data.display("en", CATALOG), source)
                self.assertEqual(data.save(), saved)

    def test_interface_disabled(self):
        self.assertEqual(marked().display("vi", CATALOG, False), "Layout")

    def test_missing_catalog_and_empty_translation(self):
        data = marked()
        self.assertEqual(data.display("vi", {}), "Layout")
        self.assertEqual(data.display("vi", {("vi", "WorkSpace", "Layout"): ""}), "Layout")

    def test_context_separates_same_spelling(self):
        self.assertEqual(marked(kind="BRUSH").display("vi", CATALOG), "Bố Cục Cọ")

    def test_unmarked_familiar_name_stays_literal(self):
        data = DataName("local:1", "WORKSPACE", "Layout")
        self.assertEqual(data.display("vi", CATALOG), "Layout")

    def test_old_localized_name_stays_literal(self):
        data = DataName.load('{"identity":"legacy:1","kind":"WORKSPACE","name":"Bố Trí"}')
        self.assertEqual(data.display("en", CATALOG), "Bố Trí")

    def test_unchanged_edit_preserves_marker(self):
        data = marked()
        data.rename_final("Layout")
        self.assertTrue(eligible(data.name, data.system_properties))

    def test_rename_away_and_back_remains_literal(self):
        data = marked()
        data.rename_final("My workspace")
        data.rename_final("Layout")
        self.assertEqual(data.display("vi", CATALOG), "Layout")
        self.assertNotIn(KEY, data.asset_properties)

    def test_rename_unicode_saved_literally(self):
        data = marked()
        data.rename_final("Bố Trí Riêng")
        restored = DataName.load(data.save())
        self.assertEqual(restored.display("en", CATALOG), "Bố Trí Riêng")

    def test_collision_peer_and_requested_id_clear(self):
        peer = marked(identity="local:peer")
        incoming = marked("Draw", "BRUSH", identity="local:incoming")
        # The final names are already chosen; check what happens to each translation note.
        peer.rename_final("Layout.001")
        incoming.rename_final("Layout")
        self.assertNotIn(KEY, peer.system_properties)
        self.assertNotIn(KEY, incoming.system_properties)

    def test_copy_after_unique_naming_does_not_restore_marker(self):
        original = marked()
        copied = original.copy("local:copy", "Layout.001")
        self.assertEqual(copied.display("vi", CATALOG), "Layout.001")
        self.assertNotIn(KEY, copied.asset_properties)
        self.assertEqual(original.display("vi", CATALOG), "Bố Trí")

    def test_user_duplicate_same_name_is_literal(self):
        copied = marked().copy("other-library:copy", "Layout", user_duplicate=True)
        self.assertEqual(copied.display("vi", CATALOG), "Layout")

    def test_identity_preserving_copy_retains_metadata(self):
        copied = marked().copy("local:1", "Layout")
        self.assertEqual(copied.display("vi", CATALOG), "Bố Trí")

    def test_append_without_and_with_collision(self):
        original = marked()
        self.assertEqual(original.copy("append:1", "Layout").display("vi", CATALOG), "Bố Trí")
        self.assertEqual(original.copy("append:2", "Layout.001").display("vi", CATALOG), "Layout.001")

    def test_save_reopen_preserves_author_intent(self):
        restored = DataName.load(marked().save())
        self.assertEqual(restored.display("vi", CATALOG), "Bố Trí")

    def test_supported_state_restore_recovers_metadata(self):
        data = marked()
        before = data.save()
        data.rename_final("Changed")
        restored = DataName.load(before)
        self.assertEqual(restored.display("vi", CATALOG), "Bố Trí")

    def test_external_asset_uses_snapshot_without_id(self):
        data = marked()
        external = ExternalAsset("library:1", data.kind, data.name, deepcopy(data.asset_properties))
        self.assertEqual(external.display("vi", CATALOG), "Bố Trí")
        self.assertEqual(external.name, "Layout")

    def test_loaded_id_does_not_infer_from_stale_asset_snapshot(self):
        data = marked()
        data.system_properties.clear()
        restored = DataName.load(data.save())
        self.assertEqual(restored.display("vi", CATALOG), "Layout")
        self.assertNotIn(KEY, restored.asset_properties)

    def test_mark_asset_after_stamping_syncs_snapshot(self):
        data = marked(asset=False)
        data.make_asset()
        self.assertEqual(data.asset_properties[KEY], data.system_properties[KEY])

    def test_unrelated_properties_survive_clear_and_sync(self):
        data = marked()
        data.system_properties["other_system_data"] = 42
        data.asset_properties["description"] = "Keep me"
        data.clear()
        self.assertEqual(data.system_properties["other_system_data"], 42)
        self.assertEqual(data.asset_properties["description"], "Keep me")

    def test_linked_read_only_display(self):
        data = marked().copy("library:linked", "Layout", linked=True)
        self.assertEqual(data.display("vi", CATALOG), "Bố Trí")
        with self.assertRaises(ValueError):
            data.rename_final("Custom")
        with self.assertRaises(ValueError):
            data.mark()

    def test_invalid_descriptors_are_literal(self):
        for descriptor in (
            None, "Layout", {}, {"version": True, "source": "Layout"},
            {"version": 2, "source": "Layout"}, {"version": 1, "source": "Other"},
            {"version": 1, "source": 42},
        ):
            with self.subTest(descriptor=descriptor):
                data = DataName("local:1", "WORKSPACE", "Layout", system_properties={KEY: descriptor})
                self.assertEqual(data.display("vi", CATALOG), "Layout")

    def test_utf8_bound_is_bytes_not_characters(self):
        for name in ("é" * 128, "\ud800", "bad\0name", ""):
            with self.subTest(name=repr(name)):
                with self.assertRaises(ValueError):
                    DataName("local:1", "WORKSPACE", name).mark()
        data = DataName("local:1", "WORKSPACE", "é" * 127 + "a")
        data.mark()
        self.assertTrue(eligible(data.name, data.system_properties))

    def test_search_matches_both_names_and_deduplicates(self):
        data = marked()
        self.assertEqual(search([data, data], "Bố Trí", "vi", CATALOG), [data.identity])
        self.assertEqual(search([data], "Layout", "vi", CATALOG), [data.identity])
        self.assertEqual(search([data], "Bố Trí", "en", CATALOG), [])

    def test_identical_labels_keep_distinct_identity_and_stable_tiebreak(self):
        first = marked(identity="id:b")
        second = marked("Second", identity="id:a")
        entries = [first, second]
        self.assertEqual(set(search(entries, "Bố Trí", "vi", CATALOG)), {"id:a", "id:b"})
        self.assertEqual([e.identity for e in presentation_order(entries, "vi", CATALOG)], ["id:a", "id:b"])

    def test_old_reader_metadata_loss_falls_back(self):
        data = marked()
        data.system_properties.clear()
        data.asset_properties.clear()
        self.assertEqual(DataName.load(data.save()).display("vi", CATALOG), "Layout")


is_main_program = __name__ == "__main__"
if is_main_program:
    unittest.main()
