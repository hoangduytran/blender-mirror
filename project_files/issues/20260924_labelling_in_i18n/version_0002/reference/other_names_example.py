"""Run in a fresh feature-branch Blender; checks names using a temporary .blend."""

from pathlib import Path
from tempfile import TemporaryDirectory

import bpy


def run_example():
    """Check four ID types, asset metadata and four kinds of contained user names."""
    has_author_api = "ui_name_translation_mark" in bpy.types.ID.bl_rna.functions
    if not has_author_api:
        raise RuntimeError("Use Blender built from the feature branch for this example.")
    view = bpy.context.preferences.view
    has_vietnamese = "vi_VN" in view.bl_rna.properties["language"].enum_items
    if not has_vietnamese:
        raise RuntimeError("This example needs Blender's existing Vietnamese language support.")
    original_language = view.language
    original_translate = view.use_translate_interface
    view.use_translate_interface = False

    mesh = bpy.data.meshes.new("Example mesh")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    obj = bpy.data.objects.new("Authored object example", mesh)
    material = bpy.data.materials.new("Authored material example")
    collection = bpy.data.collections.new("Authored collection example")
    collection.objects.link(obj)
    action = bpy.data.actions.new("Authored action example")
    cases = (
        ("materials", material, "Material", "Vật liệu mẫu"),
        ("objects", obj, "Object", "Vật thể mẫu"),
        ("collections", collection, "Collection", "Bộ sưu tập mẫu"),
        ("actions", action, "Action", "Hành động mẫu"),
    )
    names = [(collection_name, item.name) for collection_name, item, _, _ in cases]
    catalog = {(context, item.name): translated for _, item, context, translated in cases}

    modifier = obj.modifiers.new("Final Render Smooth", 'SUBSURF')
    constraint = obj.constraints.new('COPY_LOCATION')
    constraint.name = "Follow Camera Position"
    vertex_group = obj.vertex_groups.new(name="LeftArm")
    obj.shape_key_add(name="Basis")
    shape_key = obj.shape_key_add(name="Smile")
    authored_parts = (modifier, constraint, vertex_group, shape_key)
    part_names = [item.name for item in authored_parts]
    for item in authored_parts:
        assert not hasattr(item, "ui_name_translation_mark")

    material.asset_mark()
    assert not material.ui_name_is_translatable  # Asset status is not permission.
    material.asset_data.author = "Example artist"
    material.asset_data.description = "Artist's original description"
    material.asset_data.tags.new("Original tag")
    module = "other_names_example"
    bpy.app.translations.register(module, {"vi_VN": catalog})
    try:
        view.language = 'vi_VN'
        view.use_translate_interface = True
        copies = []
        for collection_name, item, _, translated in cases:
            item.use_fake_user = True
            source_name = item.name
            assert item.ui_name == source_name
            item.ui_name_translation_mark()
            assert item.ui_name == translated
            assert item.name == source_name
            item.name = source_name
            assert item.ui_name_is_translatable
            copied = item.copy()
            copied.use_fake_user = True
            assert not copied.ui_name_is_translatable
            copies.append((collection_name, copied.name))
            item.name = source_name + " Personal"
            assert not item.ui_name_is_translatable
            assert item.ui_name == item.name
            item.name = source_name
            assert not item.ui_name_is_translatable
            assert item.ui_name == source_name
            print(f"{collection_name}: opt-in translates display; copy/rename clears; saved name preserved")

        assert [item.name for item in authored_parts] == part_names
        assert modifier.type == 'SUBSURF'
        assert constraint.type == 'COPY_LOCATION'
        assert material.asset_data.author == "Example artist"
        assert material.asset_data.description == "Artist's original description"
        assert "Original tag" in material.asset_data.tags

        with TemporaryDirectory(prefix="other_names_example_") as directory:
            filepath = str(Path(directory) / "names.blend")
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
            bpy.ops.wm.open_mainfile(filepath=filepath, load_ui=False)
            for collection_name, name in names + copies:
                item = getattr(bpy.data, collection_name)[name]
                assert item.name == name
                assert item.ui_name == name
                assert not item.ui_name_is_translatable
            obj = bpy.data.objects[names[1][1]]
            material = bpy.data.materials[names[0][1]]
            assert obj.modifiers[part_names[0]].type == 'SUBSURF'
            assert obj.constraints[part_names[1]].type == 'COPY_LOCATION'
            assert obj.vertex_groups[part_names[2]].name == "LeftArm"
            assert obj.data.shape_keys.key_blocks[part_names[3]].name == "Smile"
            assert material.asset_data.author == "Example artist"
            assert material.asset_data.description == "Artist's original description"
            assert "Original tag" in material.asset_data.tags
            print("Save/reopen: all ID names, asset metadata and contained names preserved")
    finally:
        bpy.app.translations.unregister(module)
        view.language = original_language
        view.use_translate_interface = original_translate


is_main_module = __name__ == "__main__"
if is_main_module:
    run_example()
