/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include <string>

#include "BLI_string_ref.hh"

namespace blender {

struct ID;
struct IDProperty;

/** Resolve without allocation or mutation. The result is borrowed until ID/locale changes. */
StringRefNull BKE_id_ui_name_resolve(short id_type,
                                   StringRefNull name,
                                   const IDProperty *properties);
StringRefNull BKE_id_ui_name_get(const ID &id);

/** Keywords for existing fuzzy search: source and distinct display text, one result per ID. */
std::string BKE_id_ui_name_search_text(short id_type,
                                      StringRefNull name,
                                      const IDProperty *properties);

/** Explicit author opt-in. Linked and runtime-only IDs cannot be marked. */
bool BKE_id_ui_name_mark(ID &id);
bool BKE_id_ui_name_is_translatable(const ID &id);
/** Remove only the translation note, preserving other system and asset properties. */
void BKE_id_ui_name_clear(ID &id);
/** Project the ID-owned note into asset metadata for listings before import. */
void BKE_id_ui_name_asset_sync(ID &id);
/** Owned minimal property root for registration snapshots; null when no matching author note. */
IDProperty *BKE_id_ui_name_properties_copy(StringRefNull name, const IDProperty *properties);
/** Internal replacement: transfer a matching explicit note, including a deliberate absence. */
void BKE_id_ui_name_copy(ID &destination, const ID &source);
/** Validate after properties have been copied and the final name has been assigned. */
void BKE_id_ui_name_copy_finalize(ID &id);

}  // namespace blender
