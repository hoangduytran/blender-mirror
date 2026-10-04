"""Start in a separate factory-startup instance to inspect translated workspace tabs."""

import bpy


def prepare_demo():
    """Mark one example workspace and select a known test translation."""
    has_author_api = "ui_name_translation_mark" in bpy.types.ID.bl_rna.functions
    if not has_author_api:
        raise RuntimeError("This Blender lacks the shared translated-name feature.")
    has_vietnamese = "vi_VN" in bpy.context.preferences.view.bl_rna.properties["language"].enum_items
    if not has_vietnamese:
        raise RuntimeError("The demo requires Blender's Vietnamese language support.")
    workspace = bpy.context.workspace
    workspace.name = "Review workspace"
    source_name = workspace.name
    bpy.app.translations.register("ui_name_reviewer_demo", {
        "vi_VN": {("WorkSpace", source_name): "Không gian kiểm thử"},
    })
    workspace.ui_name_translation_mark()
    view = bpy.context.preferences.view
    view.show_splash = False
    view.language = 'vi_VN'
    view.use_translate_interface = True
    assert workspace.name == source_name
    assert workspace.ui_name == "Không gian kiểm thử"
    print(f"Saved name: {workspace.name}; expected tab: {workspace.ui_name}")
    print("Edit the tab: its field should start with the saved name. Cancel keeps translation.")
    print("Rename to My Review Space: the note clears. This demo does not save preferences/files.")


is_main_module = __name__ == "__main__"
if is_main_module:
    prepare_demo()
