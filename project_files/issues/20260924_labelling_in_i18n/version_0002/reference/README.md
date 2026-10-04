# Example scripts: what the name rules mean

These scripts are an explanatory model of the shared name rules. They do not install or change Blender.

Imagine a supplied workspace saved as “Layout”. Its author adds a note allowing translation. The example shows “Bố Trí” when Vietnamese is selected, and “Layout” in English. The saved name remains “Layout”.

If a user renames it, the note is removed. The chosen name then appears exactly as written, in every language. Changing the name back does not restore the note. Brushes and node-group tools follow the same rule.

## What the files do

- [name_localization.py](name_localization.py) represents items and chooses names using the proposed rules.
- [test_name_localization.py](test_name_localization.py) checks 26 cases automatically. A test passes when the example produces the expected answer.

The checks cover language changes, personal names, duplicates, name clashes, saving/reopening, asset-list notes, similar labels, search, and damaged notes.

## What they do not prove

They do not draw Blender’s interface, read `.blend` files, perform real imports, or test the keyboard. Saving uses JSON, a simple text format. Name choices are supplied to the example after they have been decided; it does not replace Blender’s existing name handling.

All 26 example tests pass. The real Blender implementation is complete and verified separately; see [final verification](../20261003_231111_verification.md) for actual Blender tests and visible checks. The reference model explains the rule and does not replace those checks.

## Optional instructions for someone running Python

From the repository’s main directory:

```sh
python3 -B -m unittest discover \
  -s project_files/issues/20260924_labelling_in_i18n/version_0002/reference \
  -p 'test_*.py' -v
```

A successful run ends with `OK`. Python is required; Blender is not required for this example. Running it does not alter your Blender preferences, startup file, or project.

See the [brush-renaming example](../20261004_001238_brush-renaming-example.md) and its runnable script.

See the [node-renaming example](../20261004_001542_node-renaming-example.md) for saved names, custom titles and node-group translation.

See [more tested name examples](../20261004_002015_other-name-examples.md) for materials, objects, collections, actions, asset details and contained names.
