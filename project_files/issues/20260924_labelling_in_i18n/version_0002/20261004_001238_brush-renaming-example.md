# A brush rename: what changes and what stays saved

This example runs on the new branch. It creates a test brush rather than changing one of your brushes. The author actions and `ui_name` property are available in this build. Reviewed bundled brushes are marked, and the required brush headers, shelves and Browser paths are connected and verified; see [final verification](20261003_231111_verification.md).

A brush has one saved name. Its translated label is chosen when needed. A real personal rename changes the saved name and removes permission to translate it.

| Step, with Vietnamese interface translation on | Saved name (`brush.name`) | Display text (`brush.ui_name`) | Translation permitted? |
| --- | --- | --- | --- |
| Create the example brush | Author brush example | Author brush example | No |
| Author marks its name | Author brush example | Cọ mẫu của tác giả | Yes |
| User renames it | Cọ yêu thích của tôi | Cọ yêu thích của tôi | No |
| Save and reopen | Cọ yêu thích của tôi | Cọ yêu thích của tôi | No |
| Rename back to the original words | Author brush example | Author brush example | No |

The last row matters: familiar words do not restore permission. An author must explicitly mark the name again.

## The short code

```python
brush = bpy.data.brushes.new("Author brush example", mode='SCULPT')
brush.ui_name_translation_mark()

# Rename normally. RNA changes the DNA-backed saved name and clears its note.
brush.name = "Cọ yêu thích của tôi"
assert not brush.ui_name_is_translatable
assert brush.ui_name == brush.name
```

Switching interface language alone leaves `brush.name` unchanged. Python lookup still uses the saved name. After an actual rename, lookup uses the new saved name; it is not an immutable identity key.

## Run the complete experiment

The [complete script](reference/brush_rename_example.py) supplies a small test translation, prints every row, saves to a temporary `.blend`, and reopens it. It uses Fake User to keep the otherwise unused test brush. After reopening, it retrieves the newly loaded brush instead of reusing the old Python reference.

Run it in a separate fresh Blender process from the repository root:

```sh
BLENDER_USER_CONFIG=/private/tmp/brush-rename-example-config \
  ../build_darwin_full/bin/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup --python-exit-code 1 \
  --python project_files/issues/20260924_labelling_in_i18n/version_0002/reference/brush_rename_example.py
```

The script uses existing Python/RNA APIs, existing DNA storage, and Blender’s existing translation support. It restores its process preferences and removes its temporary file. It reads `brush.ui_name`, which applies the shared author-permission rule. The separate [final verification](20261003_231111_verification.md) records Browser and brush-shelf coverage, including real Sculpt Mode presentation.

**Verification:** complete experiment passed on the rebuilt branch, exit 0; all five rows above matched, including real `.blend` save/reopen; the final feature gates pass in both checkouts (77 focused C++ tests and nine reviewer checks, including Blender Python integration). See [final verification](20261003_231111_verification.md) for the full results and limits.
