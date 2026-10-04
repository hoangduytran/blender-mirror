/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#include <cstring>

#include "DNA_ID.h"
#include "DNA_asset_types.h"

#include "BLI_string_utf8.hh"
#include "BLI_utildefines.hh"

#include "BKE_id_ui_name.hh"
#include "BKE_idprop.hh"
#include "BKE_idtype.hh"
#include "BKE_lib_id.hh"
#include "BKE_library.hh"

#include "BLT_translation.hh"

namespace blender {

static constexpr char descriptor_key[] = "_blender_ui_name";
static constexpr int descriptor_version = 1;

static const IDProperty *descriptor_get(const IDProperty *root)
{
  const bool has_property_group = root && root->type == IDP_GROUP;
  if (!has_property_group) {
    return nullptr;
  }
  return IDP_GetPropertyTypeFromGroup(root, descriptor_key, IDP_GROUP);
}

static bool descriptor_matches(const IDProperty *root, const StringRefNull name)
{
  const IDProperty *group = descriptor_get(root);
  const bool has_descriptor = group != nullptr;
  if (!has_descriptor) {
    return false;
  }
  const IDProperty *version = IDP_GetPropertyTypeFromGroup(group, "version", IDP_INT);
  const IDProperty *source = IDP_GetPropertyTypeFromGroup(group, "source", IDP_STRING);
  const bool has_valid_fields = version && version->data.val == descriptor_version && source &&
                                source->subtype == IDP_STRING_SUB_UTF8 && source->data.pointer;
  if (!has_valid_fields) {
    return false;
  }
  const bool has_bounded_name = !name.is_empty() && name.size() < MAX_ID_NAME - 2;
  if (!has_bounded_name) {
    return false;
  }
  const int expected_size = int(name.size()) + 1;
  const bool has_valid_storage = source->len == expected_size && source->totallen >= source->len;
  /* Compare bounded bytes including the terminator, never strlen unvalidated property data. */
  const bool matches_name = has_valid_storage &&
                            memcmp(source->data.pointer, name.c_str(), expected_size) == 0;
  return matches_name && BLI_str_utf8_invalid_byte(name.c_str(), name.size()) == -1;
}

static void descriptor_remove(IDProperty *root)
{
  const bool has_property_group = root && root->type == IDP_GROUP;
  if (!has_property_group) {
    return;
  }
  IDProperty *descriptor = IDP_GetPropertyFromGroup(root, descriptor_key);
  const bool has_descriptor = descriptor != nullptr;
  if (has_descriptor) {
    IDP_FreeFromGroup(root, descriptor);
  }
}

StringRefNull BKE_id_ui_name_resolve(const short id_type,
                                   const StringRefNull name,
                                   const IDProperty *properties)
{
  /* Unmarked names take the cheap path; the translator also protects background callers. */
  const bool should_translate = BLT_translate_iface() && descriptor_matches(properties, name);
  if (!should_translate) {
    return name;
  }
  const char *context = BKE_idtype_idcode_to_translation_context(id_type);
  const char *translated = BLT_translate_do_iface(context, name.c_str());
  const bool has_translation = translated && translated[0] != '\0';
  return has_translation ? StringRefNull(translated) : name;
}

StringRefNull BKE_id_ui_name_get(const ID &id)
{
  return BKE_id_ui_name_resolve(short(id.id_type()), BKE_id_name(id), id.system_properties);
}

std::string BKE_id_ui_name_search_text(const short id_type,
                                      const StringRefNull name,
                                      const IDProperty *properties)
{
  const StringRefNull display = BKE_id_ui_name_resolve(id_type, name, properties);
  const bool has_distinct_display = display != name;
  if (!has_distinct_display) {
    return name;
  }
  return std::string(name) + " " + std::string(display);
}

bool BKE_id_ui_name_is_translatable(const ID &id)
{
  return descriptor_matches(id.system_properties, BKE_id_name(id));
}

void BKE_id_ui_name_asset_sync(ID &id)
{
  const bool can_sync_asset = id.asset_data && (!id.asset_data->properties ||
                                                id.asset_data->properties->type == IDP_GROUP);
  if (!can_sync_asset) {
    return;
  }
  const bool has_source_note = BKE_id_ui_name_is_translatable(id);
  const bool has_current_snapshot = has_source_note &&
                                    descriptor_matches(id.asset_data->properties, BKE_id_name(id));
  if (has_current_snapshot) {
    return;
  }
  descriptor_remove(id.asset_data->properties);
  if (has_source_note) {
    const bool needs_property_group = id.asset_data->properties == nullptr;
    if (needs_property_group) {
      id.asset_data->properties = bke::idprop::create_group("AssetMetaData.properties").release();
    }
    IDP_ReplaceInGroup(id.asset_data->properties,
                       IDP_CopyProperty(descriptor_get(id.system_properties)));
  }
}

bool BKE_id_ui_name_mark(ID &id)
{
  const bool can_mark = id.id_type() != ID_WM && !ID_IS_LINKED(&id) && ID_IS_EDITABLE(&id) &&
                        BKE_id_name(id)[0] != '\0' &&
                        (!id.system_properties || id.system_properties->type == IDP_GROUP) &&
                        (!id.asset_data || !id.asset_data->properties ||
                         id.asset_data->properties->type == IDP_GROUP);
  if (!can_mark) {
    return false;
  }
  const bool has_valid_text = BLI_str_utf8_invalid_byte(BKE_id_name(id),
                                                        strlen(BKE_id_name(id))) == -1;
  if (!has_valid_text) {
    return false;
  }
  const bool has_source_note = BKE_id_ui_name_is_translatable(id);
  if (!has_source_note) {
    auto descriptor = bke::idprop::create_group(descriptor_key);
    IDP_ReplaceInGroup(descriptor.get(),
                       bke::idprop::create("version", int32_t(descriptor_version)).release());
    IDP_ReplaceInGroup(descriptor.get(),
                       bke::idprop::create("source", StringRefNull(BKE_id_name(id))).release());
    const bool needs_property_group = id.system_properties == nullptr;
    if (needs_property_group) {
      id.system_properties = bke::idprop::create_group("ID.system_properties").release();
    }
    IDP_ReplaceInGroup(id.system_properties, descriptor.release());
  }
  BKE_id_ui_name_asset_sync(id);
  return true;
}

void BKE_id_ui_name_clear(ID &id)
{
  descriptor_remove(id.system_properties);
  BKE_id_ui_name_asset_sync(id);
}

IDProperty *BKE_id_ui_name_properties_copy(const StringRefNull name, const IDProperty *properties)
{
  const bool has_valid_note = descriptor_matches(properties, name);
  if (!has_valid_note) {
    return nullptr;
  }
  auto root = bke::idprop::create_group("UI name registration");
  IDP_ReplaceInGroup(root.get(), IDP_CopyProperty(descriptor_get(properties)));
  return root.release();
}

void BKE_id_ui_name_copy(ID &destination, const ID &source)
{
  const bool is_same_id = &destination == &source;
  if (is_same_id) {
    return;
  }
  const bool can_transfer_note = BKE_id_ui_name_is_translatable(source) &&
                                 STREQ(BKE_id_name(destination), BKE_id_name(source));
  const bool has_valid_root = !destination.system_properties ||
                              destination.system_properties->type == IDP_GROUP;
  if (!has_valid_root) {
    return;
  }
  descriptor_remove(destination.system_properties);
  if (can_transfer_note) {
    const bool needs_root = destination.system_properties == nullptr;
    if (needs_root) {
      destination.system_properties = bke::idprop::create_group("ID.system_properties").release();
    }
    IDP_ReplaceInGroup(destination.system_properties,
                       IDP_CopyProperty(descriptor_get(source.system_properties)));
  }
  BKE_id_ui_name_asset_sync(destination);
}

void BKE_id_ui_name_copy_finalize(ID &id)
{
  const bool has_source_note = BKE_id_ui_name_is_translatable(id);
  if (!has_source_note) {
    descriptor_remove(id.system_properties);
  }
  BKE_id_ui_name_asset_sync(id);
}

}  // namespace blender
