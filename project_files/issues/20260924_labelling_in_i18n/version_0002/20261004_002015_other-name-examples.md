# More names checked in the actual Blender build

The [runnable experiment](reference/other_names_example.py) passes on the rebuilt feature branch. An independent tester also ran it successfully with separate preferences.

## What passed?

| Example | Result |
| --- | --- |
| Material | Saved name stays literal until explicitly marked. Its chosen display text then translates. |
| Object | Uses the same shared rule; switching language leaves its saved name alone. |
| Collection | Uses the same shared rule, including after copying and renaming. |
| Action | Uses the same shared rule; the saved animation name remains independent of language. |
| Material marked as an asset | Asset status alone does not permit translation. Author, description and tag remain unchanged through marking, renaming and saving. |
| Subdivision modifier | “Final Render Smooth” remains the saved name; the modifier type stays `SUBSURF`. |
| Copy Location constraint | “Follow Camera Position” remains the saved name; its type stays `COPY_LOCATION`. |
| Vertex group | “LeftArm” survives language changes and save/reopen. |
| Shape key | “Smile” survives language changes and save/reopen. |

For all four ID types, the experiment checks the complete shared sequence:

1. An unmarked name stays literal.
2. An author mark permits the supplied test translation; the saved name stays unchanged.
3. Assigning exactly the same saved name keeps permission.
4. A user copy has no translation permission.
5. A real personal rename removes permission.
6. Renaming back does not restore it.
7. Save/reopen preserves the final names and cleared permission, including the copies.

## The two kinds of name

Materials, objects, collections and actions are ID data-blocks. This branch exposes the shared helper through their inherited RNA properties and actions:

```python
material.ui_name_translation_mark()
material.name = "My Paint"
assert not material.ui_name_is_translatable
assert material.ui_name == "My Paint"
```

A modifier, constraint, vertex group or individual shape key is a separate part of its owning data. Each keeps its own existing name property. These individual fields do not gain the shared ID author actions. A Shape Key data-block and its individual key blocks are different levels of data.

The experiment verifies actual RNA values and `.blend` persistence. The required display paths are implemented and checked separately in [final verification](20261003_231111_verification.md). Reading `item.ui_name` in this experiment alone does not prove a particular editor draws that text.

## Run it

Run in a separate fresh process from the repository root; it creates and reopens a temporary project. Fake User keeps the unused example ID items. After reopening, it retrieves the loaded items again before checking them.

```sh
BLENDER_USER_CONFIG=/private/tmp/other-names-example-config \
  ../build_darwin_full/bin/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup --python-exit-code 1 \
  --python project_files/issues/20260924_labelling_in_i18n/version_0002/reference/other_names_example.py
```

The supplied translations are a small test list registered with Blender’s existing translation system. They are not new factory translations. Translation categories come from the current ID-type definitions: `Material`, `Object`, `Collection`, and `Action`.

**Evidence:** root and independent runs exit 0. Independent log: `/private/tmp/id-ui-name-other-example.log`. The independent reviewer confirmed DNA/RNA/bpy scope and save/reopen reference handling. No production changes or new libraries.

## Still outside this experiment

Bone names, asset catalogs, scenes, worlds, images, online/external asset browsing, search/sorting, and actual screen rendering were not tested here. The separate [final verification](20261003_231111_verification.md) covers the required Browser/search and visible checks. Other examples listed here are outside this experiment and are not required feature blockers. Catalogs and individual bone/socket names need their own design review before adding translation permission; the current shared ID note does not cover them.
