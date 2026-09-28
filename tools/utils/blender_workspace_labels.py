#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Mark reviewed bundled workspace labels after resaving with the current DNA.

Run on a staged source-tree layout, then review before replacing bundled assets:
    python tools/utils/blender_workspace_labels.py /path/to/staged/root
    python tools/utils/blender_workspace_labels.py /path/to/staged/root --check

This is offline asset maintenance, not runtime name-based migration. The tool
never renames IDs or clears custom labels. Unknown entries remain literal.
"""

import argparse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "modules"))
import blendfile


# Explicitly reviewed bases per asset; do not derive this list from loaded names.
CANONICAL_NAMES = {
    "release/datafiles/startup.blend": {
        "Animation", "Compositing", "Geometry Nodes", "Layout", "Modeling",
        "Rendering", "Scripting", "Sculpting", "Shading", "Texture Paint", "UV Editing",
    },
    "scripts/startup/bl_app_templates_system/2D_Animation/startup.blend": {
        "2D Animation", "2D Full Canvas",
    },
    "scripts/startup/bl_app_templates_system/Sculpting/startup.blend": {
        "Sculpting", "Shading",
    },
    "scripts/startup/bl_app_templates_system/Storyboarding/startup.blend": {
        "Storyboarding", "Video Editing",
    },
    "scripts/startup/bl_app_templates_system/VFX/startup.blend": {
        "Compositing", "Masking", "Motion Tracking", "Rendering",
    },
    "scripts/startup/bl_app_templates_system/Video_Editing/startup.blend": {
        "Compositing", "Rendering", "Video Editing",
    },
}


def prepared_workspaces(blend, canonical_names):
    """Validate the whole asset before allowing any metadata writes."""
    has_reviewed_names = bool(canonical_names)
    if not has_reviewed_names:
        raise ValueError("A reviewed per-asset manifest is required")

    prepared = []
    for block in blend.find_blocks_from_code(b"WS"):
        name = block.get((b"id", b"name"))[2:]
        source = block.get(b"label_source", default=None)
        custom = block.get(b"custom_display_name", default=None)
        has_label_fields = source is not None and custom is not None
        if not has_label_fields:
            raise ValueError("Resave with the new DNA first: " + name)
        has_custom_label = custom != ""
        if has_custom_label:
            raise ValueError("Review the existing custom label: " + name)
        prepared.append((block, name))

    missing_names = canonical_names - {name for _, name in prepared}
    has_missing_names = bool(missing_names)
    if has_missing_names:
        raise ValueError("Missing manifest names: " + ", ".join(sorted(missing_names)))
    return prepared


def process_asset(path, canonical_names, *, check_only):
    access = "rb" if check_only else "r+b"
    with blendfile.open_blend(str(path), access=access) as blend:
        for block, name in prepared_workspaces(blend, canonical_names):
            is_reviewed_canonical = name in canonical_names
            expected_source = 1 if is_reviewed_canonical else 0
            has_expected_source = block.get(b"label_source") == expected_source
            if check_only:
                if not has_expected_source:
                    raise ValueError("Unexpected label source: " + name)
            elif not has_expected_source:
                block.set(b"label_source", bytes([expected_source]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Root containing the six prepared asset paths")
    parser.add_argument("--check", action="store_true", help="Verify without changing files")
    args = parser.parse_args()

    # Preflight every asset before changing any file in the staged set.
    for relative_path, names in CANONICAL_NAMES.items():
        with blendfile.open_blend(str(args.root / relative_path)) as blend:
            prepared_workspaces(blend, names)
    for relative_path, names in CANONICAL_NAMES.items():
        path = args.root / relative_path
        process_asset(path, names, check_only=args.check)
        process_asset(path, names, check_only=True)
        print("Verified:", relative_path)


if __name__ == "__main__":
    main()
