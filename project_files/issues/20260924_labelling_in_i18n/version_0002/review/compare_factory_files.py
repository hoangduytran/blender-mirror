# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Read-only canonical RNA comparison of approved factory assets and their backups."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy

EXCLUDED = {
    'rna_type', 'id_data', 'ui_name', 'ui_name_is_translatable', 'filepath',
    'users', 'session_uid', 'is_updated', 'is_updated_data', 'is_updated_transform',
    'is_evaluated', 'original', 'is_runtime_data', 'is_library_indirect', 'icon_id',
}


def canonical_scalar(value):
    is_float = isinstance(value, float)
    if is_float:
        is_nan = math.isnan(value)
        if is_nan:
            return 'NaN'
        is_infinite = math.isinf(value)
        if is_infinite:
            return 'Infinity' if value > 0 else '-Infinity'
    is_set = isinstance(value, set)
    if is_set:
        return sorted(value)
    return value


def id_reference(item):
    return {'id_type': item.bl_rna.identifier, 'name': item.name,
            'library': Path(item.library.filepath).name if item.library else None}


def pointer_reference(item):
    result = {'type': item.bl_rna.identifier}
    for key in ('name', 'identifier', 'is_output'):
        has_identity_field = hasattr(item, key)
        if has_identity_field:
            result[key] = getattr(item, key)
    return result


def properties(item):
    try:
        result = {}
        for key in sorted(item.keys()):
            is_author_note = key == '_blender_ui_name'
            if not is_author_note:
                result[key] = convert_custom(item[key])
        return result
    except (AttributeError, TypeError):
        return {}


def convert_custom(value):
    is_id = isinstance(value, bpy.types.ID)
    if is_id:
        return id_reference(value)
    has_dictionary_values = hasattr(value, 'to_dict')
    if has_dictionary_values:
        result = {}
        for key, item in sorted(value.to_dict().items()):
            is_author_note = key == '_blender_ui_name'
            if not is_author_note:
                result[key] = convert_custom(item)
        return result
    has_list_values = hasattr(value, 'to_list')
    if has_list_values:
        return [convert_custom(item) for item in value.to_list()]
    is_sequence = isinstance(value, (tuple, list))
    if is_sequence:
        return [convert_custom(item) for item in value]
    return canonical_scalar(value)


def snapshot(item, ancestry=(), expand_id=False):
    is_absent = item is None
    if is_absent:
        return None
    is_id_reference = isinstance(item, bpy.types.ID) and not expand_id
    if is_id_reference:
        return id_reference(item)
    is_preview = item.bl_rna.identifier == 'ImagePreview'
    if is_preview:
        return {'image_size': list(item.image_size), 'icon_size': list(item.icon_size),
                'image_custom': item.is_image_custom, 'icon_custom': item.is_icon_custom,
                'image_hash': hashlib.sha256(json.dumps(list(item.image_pixels)).encode()).hexdigest(),
                'icon_hash': hashlib.sha256(json.dumps(list(item.icon_pixels)).encode()).hexdigest()}
    pointer = item.as_pointer()
    is_recursive_reference = pointer in ancestry
    if is_recursive_reference:
        return pointer_reference(item)
    ancestry = ancestry + (pointer,)
    result = {'type': item.bl_rna.identifier, 'properties': properties(item)}
    for prop in item.bl_rna.properties:
        name = prop.identifier
        is_excluded = name in EXCLUDED
        if is_excluded:
            continue
        try:
            value = getattr(item, name)
            is_scalar = prop.type in {'BOOLEAN', 'INT', 'FLOAT', 'STRING', 'ENUM'}
            is_collection = prop.type == 'COLLECTION'
            is_pointer = prop.type == 'POINTER'
            if is_scalar:
                result[name] = ([canonical_scalar(entry) for entry in value] if getattr(prop, "is_array", False)
                                else canonical_scalar(value))
            elif is_collection:
                result[name] = [snapshot(entry, ancestry) for entry in value]
            elif is_pointer:
                is_graph_reference = isinstance(value, (bpy.types.Node, bpy.types.NodeSocket))
                if is_graph_reference:
                    result[name] = pointer_reference(value)
                else:
                    result[name] = snapshot(value, ancestry)
        except Exception as error:
            # Failure to read a stored setting must fail the comparison, rather than hide it.
            raise RuntimeError(f'Cannot snapshot {item.bl_rna.identifier}.{name}: {error}') from error
    return result


def file_snapshot(filepath):
    bpy.ops.wm.open_mainfile(filepath=str(filepath))
    ids = sorted([*bpy.data.brushes, *bpy.data.node_groups], key=lambda item: (item.bl_rna.identifier, item.name, Path(item.library.filepath).name if item.library else ''))
    return [snapshot(item, expand_id=True) for item in ids]


def differences(left, right, path=''):
    has_different_type = type(left) != type(right)
    if has_different_type:
        return [{'path': path, 'before': left, 'after': right}]
    is_mapping = isinstance(left, dict)
    if is_mapping:
        result = []
        for key in sorted(left.keys() | right.keys()):
            has_missing_key = key not in left or key not in right
            if has_missing_key:
                result.append({'path': path + '.' + key, 'before': left.get(key), 'after': right.get(key)})
            else:
                result.extend(differences(left[key], right[key], path + '.' + key))
        return result
    is_list = isinstance(left, list)
    if is_list:
        result = []
        has_different_length = len(left) != len(right)
        if has_different_length:
            result.append({'path': path + '.length', 'before': len(left), 'after': len(right)})
        for index, (before, after) in enumerate(zip(left, right)):
            result.extend(differences(before, after, f'{path}[{index}]'))
        return result
    return [] if left == right else [{'path': path, 'before': left, 'after': right}]


def main():
    """Compare actual source files to a separate, untouched baseline directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-dir', required=True, type=Path,
                        help='Directory containing the original assets/brushes and assets/nodes files')
    parser.add_argument('--source-dir', type=Path, default=Path(__file__).resolve().parents[5])
    parser.add_argument('--output-dir', required=True, type=Path)
    has_script_arguments = '--' in sys.argv
    arguments = sys.argv[sys.argv.index('--') + 1:] if has_script_arguments else []
    args = parser.parse_args(arguments)
    baseline_root = args.baseline_dir.resolve()
    source_root = args.source_dir.resolve()
    is_same_directory = baseline_root == source_root
    if is_same_directory:
        parser.error('Use a separate original baseline directory, not the changed source directory')
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    files = json.loads((source_root / 'tools/utils/blend_ui_name_factory_files.json').read_text())
    reports = []
    for filename in files:
        backup_path = baseline_root / filename
        source_path = source_root / filename
        before_hash = hashlib.sha256(backup_path.read_bytes()).hexdigest()
        source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        before = file_snapshot(backup_path)
        after = file_snapshot(source_path)
        changes = differences(before, after)
        assert hashlib.sha256(backup_path.read_bytes()).hexdigest() == before_hash
        assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source_hash
        report = {'file': filename, 'ids': len(before), 'differences': changes,
                  'before_sha256': before_hash, 'source_sha256': source_hash}
        reports.append(report)
        (output / (Path(filename).stem + '.json')).write_text(json.dumps(report, indent=2))
        print(filename, len(before), 'IDs', len(changes), 'differences', flush=True)
    summary = {'passed': all(not report['differences'] for report in reports), 'files': reports,
               'excluded_rna_properties': sorted(EXCLUDED),
               'excluded_custom_properties': ['_blender_ui_name'],
               'scope': 'All RNA-accessible settings on brush/node-group IDs and their owned nested RNA data; node topology, sockets, interface and asset catalog metadata. ID references use type/name/library basename. Stored preview pixels are hashed; non-RNA DNA fields are not compared.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2))
    has_differences = not summary['passed']
    if has_differences:
        raise AssertionError('Factory rewrite changed the recorded RNA data; see summary.json')


is_main_module = __name__ == '__main__'
if is_main_module:
    main()
