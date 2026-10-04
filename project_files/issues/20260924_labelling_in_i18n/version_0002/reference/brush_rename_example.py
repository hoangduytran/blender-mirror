"""Run in a fresh Blender built from this branch; creates only a temporary file."""

from pathlib import Path
from tempfile import TemporaryDirectory

import bpy


def show(brush, step):
    print(f"{step}: saved={brush.name!r}; displayed={brush.ui_name!r}; "
          f"marked={brush.ui_name_is_translatable}")


def run_example():
    has_author_api = "ui_name_translation_mark" in bpy.types.ID.bl_rna.functions
    if not has_author_api:
        raise RuntimeError("Use Blender built from the feature branch for this example.")
    view = bpy.context.preferences.view
    has_vietnamese = "vi_VN" in view.bl_rna.properties["language"].enum_items
    if not has_vietnamese:
        raise RuntimeError("This example needs Blender's existing Vietnamese language support.")
    original_language = view.language
    original_translate = view.use_translate_interface
    module = "brush_rename_example"
    brush = bpy.data.brushes.new("Author brush example", mode='SCULPT')
    source_name = brush.name
    brush.use_fake_user = True  # Keep this unused example brush when saving.
    bpy.app.translations.register(module, {
        "vi_VN": {("Brush", source_name): "Cọ mẫu của tác giả"},
    })
    try:
        view.language = 'vi_VN'
        view.use_translate_interface = True
        show(brush, "Unmarked")
        brush.ui_name_translation_mark()
        show(brush, "Author marks the name")
        assert brush.name == source_name
        assert brush.ui_name == "Cọ mẫu của tác giả"

        brush.name = "Cọ yêu thích của tôi"  # A real personal rename through RNA.
        personal_name = brush.name
        show(brush, "User renames")
        assert not brush.ui_name_is_translatable
        assert brush.ui_name == personal_name

        with TemporaryDirectory(prefix="brush_rename_example_") as directory:
            filepath = str(Path(directory) / "brush.blend")
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
            bpy.ops.wm.open_mainfile(filepath=filepath, load_ui=False)
            brush = bpy.data.brushes[personal_name]  # Get the newly loaded item.
            show(brush, "Save and reopen")
            assert not brush.ui_name_is_translatable
            assert brush.ui_name == personal_name

            brush.name = source_name
            show(brush, "Rename back")
            assert not brush.ui_name_is_translatable
            assert brush.ui_name == source_name
    finally:
        bpy.app.translations.unregister(module)
        view.language = original_language
        view.use_translate_interface = original_translate


is_main_module = __name__ == "__main__"
if is_main_module:
    run_example()
