"""Run in a fresh feature-branch Blender; saves only a temporary example file."""

from pathlib import Path
from tempfile import TemporaryDirectory

import bpy


def run_example():
    """Demonstrate saved node names, custom titles and marked group display names."""
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

    material = bpy.data.materials.new("Node rename example")
    material.use_fake_user = True
    material.node_tree.nodes.clear()
    node = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    node.name = "Skin Shader"  # Saved lookup name, changed through RNA.
    node.label = "Human Skin"  # Saved custom title; does not rename the node.
    assert material.node_tree.nodes["Skin Shader"] == node
    assert node.bl_idname == "ShaderNodeBsdfPrincipled"
    print(f"Node: name={node.name!r}; custom title={node.label!r}; type={node.bl_idname!r}")

    group = bpy.data.node_groups.new("Author node-group example", 'GeometryNodeTree')
    group.use_fake_user = True
    socket = group.interface.new_socket(name="Density", in_out='INPUT',
                                        socket_type='NodeSocketFloat')
    source_name = group.name
    module = "node_rename_example"
    bpy.app.translations.register(module, {
        "vi_VN": {("NodeTree", source_name): "Nhóm nút mẫu của tác giả"},
    })
    try:
        view.language = 'vi_VN'
        view.use_translate_interface = True
        assert node.name == "Skin Shader"
        assert node.label == "Human Skin"
        assert node.bl_idname == "ShaderNodeBsdfPrincipled"
        assert socket.name == "Density"
        assert group.ui_name == source_name  # No permission yet.

        group.ui_name_translation_mark()
        assert group.name == source_name
        assert group.ui_name == "Nhóm nút mẫu của tác giả"
        print(f"Marked group: saved={group.name!r}; displayed={group.ui_name!r}")
        group.name = "My Tree Tool"
        assert not group.ui_name_is_translatable
        assert group.ui_name == "My Tree Tool"
        print(f"Renamed group: saved={group.name!r}; displayed={group.ui_name!r}")

        material_name = material.name
        group_name = group.name
        with TemporaryDirectory(prefix="node_rename_example_") as directory:
            filepath = str(Path(directory) / "nodes.blend")
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
            bpy.ops.wm.open_mainfile(filepath=filepath, load_ui=False)
            material = bpy.data.materials[material_name]
            node = material.node_tree.nodes["Skin Shader"]
            group = bpy.data.node_groups[group_name]
            assert node.name == "Skin Shader"
            assert node.label == "Human Skin"
            assert node.bl_idname == "ShaderNodeBsdfPrincipled"
            assert group.ui_name == "My Tree Tool"
            assert not group.ui_name_is_translatable
            assert group.interface.items_tree["Density"].name == "Density"
            print("Reopened: node name, custom title, type, group name and socket name preserved")
            group.name = source_name
            assert not group.ui_name_is_translatable
            assert group.ui_name == source_name
            print("Group renamed back: translation permission remains off")
    finally:
        bpy.app.translations.unregister(module)
        view.language = original_language
        view.use_translate_interface = original_translate


is_main_module = __name__ == "__main__"
if is_main_module:
    run_example()
