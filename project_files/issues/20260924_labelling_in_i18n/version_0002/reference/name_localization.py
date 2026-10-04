"""Small example of the proposed name rules; this does not run Blender.

An author note allows a supplied name to be translated. A real rename removes
that permission. The example uses its own translation list and saved text, so it
does not change Blender, user preferences, or project files.
"""

from copy import deepcopy
from dataclasses import dataclass, field
import json


KEY = "_blender_ui_name"
VERSION = 1
MAX_NAME_BYTES = 255  # Blender reserves one extra byte to mark the end of the saved name.
CONTEXTS = {"WORKSPACE": "WorkSpace", "BRUSH": "Brush", "NODETREE": "NodeTree"}


def valid_name(name):
    has_valid_text = isinstance(name, str) and bool(name) and "\0" not in name
    if not has_valid_text:
        return False
    try:
        return len(name.encode("utf-8")) <= MAX_NAME_BYTES
    except UnicodeEncodeError:
        return False


def eligible(raw_name, properties):
    can_read_note = valid_name(raw_name) and isinstance(properties, dict)
    if not can_read_note:
        return False
    descriptor = properties.get(KEY)
    has_note = isinstance(descriptor, dict)
    if not has_note:
        return False
    return (
        type(descriptor.get("version")) is int
        and descriptor["version"] == VERSION
        and type(descriptor.get("source")) is str
        and descriptor["source"] == raw_name
    )


def resolve(raw_name, kind, properties, language, interface_enabled, catalog):
    should_translate = interface_enabled and eligible(raw_name, properties)
    if not should_translate:
        return raw_name
    # If the item type has no special translation category, use the general one.
    context = CONTEXTS.get(kind, "*")
    translated = catalog.get((language, context, raw_name))
    return translated if isinstance(translated, str) and translated else raw_name


@dataclass
class DataName:
    identity: str
    kind: str
    name: str
    linked: bool = False
    system_properties: dict = field(default_factory=dict)
    asset_properties: dict | None = None

    def sync_asset(self):
        needs_asset_properties = self.asset_properties is None
        if needs_asset_properties:
            return
        self.asset_properties.pop(KEY, None)
        has_source_note = eligible(self.name, self.system_properties)
        if has_source_note:
            self.asset_properties[KEY] = deepcopy(self.system_properties[KEY])

    def mark(self):
        can_mark = not self.linked and valid_name(self.name)
        if not can_mark:
            raise ValueError("Author stamp requires a valid editable source name")
        self.system_properties[KEY] = {"version": VERSION, "source": self.name}
        self.sync_asset()

    def clear(self):
        self.system_properties.pop(KEY, None)
        self.sync_asset()

    def rename_final(self, final_name):
        """Apply a name already chosen; this example does not decide name clashes."""
        is_read_only = self.linked
        if is_read_only:
            raise ValueError("Linked data is read-only")
        has_valid_name = valid_name(final_name)
        if not has_valid_name:
            raise ValueError("Invalid final name")
        has_name_changed = final_name != self.name
        if has_name_changed:
            self.name = final_name
            self.clear()

    def finalize_binding(self):
        has_source_note = eligible(self.name, self.system_properties)
        if not has_source_note:
            self.system_properties.pop(KEY, None)
        self.sync_asset()

    def copy(self, identity, final_name, user_duplicate=False, linked=False):
        has_valid_name = valid_name(final_name)
        if not has_valid_name:
            raise ValueError("Invalid copied name")
        result = deepcopy(self)
        result.identity = identity
        result.name = final_name
        result.linked = linked
        is_user_duplicate = user_duplicate
        if is_user_duplicate:
            result.clear()
        else:
            result.finalize_binding()
        return result

    def make_asset(self):
        is_read_only = self.linked
        if is_read_only:
            raise ValueError("Linked data is read-only")
        needs_asset_properties = self.asset_properties is None
        if needs_asset_properties:
            self.asset_properties = {}
        self.sync_asset()

    def display(self, language, catalog, interface_enabled=True):
        return resolve(self.name, self.kind, self.system_properties,
                       language, interface_enabled, catalog)

    def save(self):
        """Save example data as text; leave automatic translations out of the file."""
        return json.dumps(self.__dict__, ensure_ascii=False, sort_keys=True)

    @classmethod
    def load(cls, payload):
        result = cls(**json.loads(payload))
        result.finalize_binding()
        return result


@dataclass
class ExternalAsset:
    identity: str
    kind: str
    name: str
    properties: dict

    def display(self, language, catalog, interface_enabled=True):
        return resolve(self.name, self.kind, self.properties,
                       language, interface_enabled, catalog)


def search(entries, query, language, catalog, interface_enabled=True):
    """Find saved or displayed names; return each item once using its own reference."""
    query = query.casefold()
    found = []
    seen = set()
    for entry in entries:
        visible = entry.display(language, catalog, interface_enabled)
        matches_query = query in entry.name.casefold() or query in visible.casefold()
        if matches_query:
            is_new_result = entry.identity not in seen
            if is_new_result:
                found.append(entry.identity)
                seen.add(entry.identity)
    return found


def presentation_order(entries, language, catalog):
    """Sort a list by displayed names; workspace tabs keep their own chosen order."""
    return sorted(entries, key=lambda entry: (
        entry.display(language, catalog).casefold(), entry.identity))
