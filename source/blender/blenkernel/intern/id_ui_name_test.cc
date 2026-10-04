/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_asset.hh"
#include "BKE_global.hh"
#include "BKE_gtest_base.hh"
#include "BKE_id_ui_name.hh"
#include "BKE_idprop.hh"
#include "BKE_lib_id.hh"
#include "BKE_main.hh"

#include "DNA_ID.h"
#include "DNA_asset_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"

#include "testing/testing.h"

namespace blender::bke::tests {

class IDUINameTest : public BlenderGTestBase {
 protected:
  Main *bmain_ = nullptr;
  eUserpref_Translation_Flags translation_flags_;

  void SetUp() override
  {
    bmain_ = BKE_main_new();
    translation_flags_ = U.transopts;
    U.transopts &= ~USER_TR_IFACE;
  }

  void TearDown() override
  {
    BKE_main_free(bmain_);
    U.transopts = translation_flags_;
  }

  ID &new_id(const short type = ID_OB, const char *name = "Layout")
  {
    return *static_cast<ID *>(BKE_id_new(bmain_, type, name));
  }

  static IDProperty *descriptor(const ID &id)
  {
    return IDP_GetPropertyFromGroup_null(id.system_properties, "_blender_ui_name");
  }

  static IDProperty *source_property(const ID &id)
  {
    return IDP_GetPropertyFromGroup(descriptor(id), "source");
  }

  static IDProperty *asset_descriptor(const ID &id)
  {
    return IDP_GetPropertyFromGroup_null(id.asset_data->properties, "_blender_ui_name");
  }
};

TEST_F(IDUINameTest, FamiliarUnmarkedNamesRemainLiteral)
{
  ID &id = new_id(ID_WS);
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
  EXPECT_EQ(id.system_properties, nullptr);
}

TEST_F(IDUINameTest, ExplicitMarkSupportsSeveralDataTypes)
{
  for (const short type : {ID_WS, ID_BR, ID_NT, ID_OB}) {
    ID &id = new_id(type);
    ASSERT_TRUE(BKE_id_ui_name_mark(id));
    EXPECT_TRUE(BKE_id_ui_name_is_translatable(id));
    ASSERT_NE(descriptor(id), nullptr);
    EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
    EXPECT_STREQ(id.name + 2, "Layout");
  }
}

TEST_F(IDUINameTest, WindowManagerCannotBeMarked)
{
  /* A window manager needs full application setup to be freed through Main. */
  wmWindowManager manager{};
  ID &id = manager.id;
  id.name[0] = 'W';
  id.name[1] = 'M';
  EXPECT_FALSE(BKE_id_ui_name_mark(id));
  EXPECT_EQ(descriptor(id), nullptr);
}

TEST_F(IDUINameTest, LinkedDataCannotBeMarked)
{
  ID &id = new_id();
  id.lib = static_cast<Library *>(BKE_id_new(bmain_, ID_LI, "Library"));
  EXPECT_FALSE(BKE_id_ui_name_mark(id));
  EXPECT_EQ(descriptor(id), nullptr);
  /* Restore the original Main membership before freeing its name map. */
  id.lib = nullptr;
}

TEST_F(IDUINameTest, RepeatedMarkAndClearPreserveOtherProperties)
{
  ID &id = new_id();
  id.system_properties = idprop::create_group("System").release();
  ASSERT_TRUE(IDP_AddToGroup(id.system_properties, idprop::create("unrelated", 42).release()));
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  BKE_id_ui_name_clear(id);
  BKE_id_ui_name_clear(id);
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(descriptor(id), nullptr);
  ASSERT_NE(IDP_GetPropertyFromGroup(id.system_properties, "unrelated"), nullptr);
  EXPECT_EQ(IDP_int_get(IDP_GetPropertyFromGroup(id.system_properties, "unrelated")), 42);
}

TEST_F(IDUINameTest, UnchangedRenameKeepsMark)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  BKE_libblock_rename(*bmain_, id, "Layout", IDNewNameMode::RenameExistingNever);
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(id));
}

TEST_F(IDUINameTest, RenameAwayAndBackRemainsLiteral)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  BKE_libblock_rename(*bmain_, id, "Personal", IDNewNameMode::RenameExistingNever);
  EXPECT_EQ(descriptor(id), nullptr);
  BKE_libblock_rename(*bmain_, id, "Layout", IDNewNameMode::RenameExistingNever);
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(descriptor(id), nullptr);
}

TEST_F(IDUINameTest, OrdinaryCollisionClearsOnlyChangedItem)
{
  ID &existing = new_id(ID_OB, "Layout");
  ID &requested = new_id(ID_OB, "Other");
  ASSERT_TRUE(BKE_id_ui_name_mark(existing));
  ASSERT_TRUE(BKE_id_ui_name_mark(requested));
  BKE_libblock_rename(*bmain_, requested, "Layout", IDNewNameMode::RenameExistingNever);
  EXPECT_STREQ(existing.name + 2, "Layout");
  EXPECT_STREQ(requested.name + 2, "Layout.001");
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(existing));
  EXPECT_EQ(descriptor(requested), nullptr);
}

TEST_F(IDUINameTest, UnchangedCollisionKeepsMark)
{
  new_id(ID_OB, "Layout");
  ID &id = new_id(ID_OB, "Layout.001");
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  BKE_libblock_rename(*bmain_, id, "Layout", IDNewNameMode::RenameExistingNever);
  EXPECT_STREQ(id.name + 2, "Layout.001");
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(id));
}

TEST_F(IDUINameTest, ForcedCollisionClearsBothChangedItems)
{
  ID &existing = new_id(ID_OB, "Layout");
  ID &requested = new_id(ID_OB, "Other");
  ASSERT_TRUE(BKE_id_ui_name_mark(existing));
  ASSERT_TRUE(BKE_id_ui_name_mark(requested));
  BKE_libblock_rename(*bmain_, requested, "Layout", IDNewNameMode::RenameExistingAlways);
  EXPECT_STREQ(existing.name + 2, "Layout.001");
  EXPECT_STREQ(requested.name + 2, "Layout");
  EXPECT_EQ(descriptor(existing), nullptr);
  EXPECT_EQ(descriptor(requested), nullptr);
}

TEST_F(IDUINameTest, RealCopyCannotRestoreNoteAfterNameCollision)
{
  ID &original = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(original));
  ID *copy = BKE_id_copy(bmain_, &original);
  ASSERT_NE(copy, nullptr);
  EXPECT_STREQ(copy->name + 2, "Layout.001");
  EXPECT_EQ(descriptor(*copy), nullptr);
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(original));
}

TEST_F(IDUINameTest, TemporaryCopyKeepsValidNote)
{
  ID &original = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(original));
  ID *copy = BKE_id_copy_ex(nullptr, &original, nullptr, LIB_ID_COPY_LOCALIZE);
  ASSERT_NE(copy, nullptr);
  EXPECT_STREQ(copy->name + 2, "Layout");
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(*copy));
  BKE_id_free(nullptr, copy);
}

TEST_F(IDUINameTest, AssetSnapshotPreservesOtherMetadataAndClearsTogether)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  id.asset_data = BKE_asset_metadata_create();
  id.asset_data->properties = idprop::create_group("Asset").release();
  ASSERT_TRUE(IDP_AddToGroup(id.asset_data->properties, idprop::create("rating", 5).release()));
  BKE_id_ui_name_asset_sync(id);
  ASSERT_NE(asset_descriptor(id), nullptr);
  EXPECT_NE(asset_descriptor(id), descriptor(id));
  EXPECT_EQ(BKE_id_ui_name_resolve(ID_OB, "Layout", id.asset_data->properties), "Layout");
  BKE_id_ui_name_clear(id);
  EXPECT_EQ(asset_descriptor(id), nullptr);
  EXPECT_EQ(IDP_int_get(IDP_GetPropertyFromGroup(id.asset_data->properties, "rating")), 5);
}

TEST_F(IDUINameTest, AssetSnapshotCannotRestoreMissingMainNote)
{
  ID &id = new_id();
  id.asset_data = BKE_asset_metadata_create();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  ASSERT_NE(asset_descriptor(id), nullptr);
  IDP_FreeFromGroup(id.system_properties, descriptor(id));
  BKE_id_ui_name_copy_finalize(id);
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(asset_descriptor(id), nullptr);
}

TEST_F(IDUINameTest, AssetRenameRemovesBothNotes)
{
  ID &id = new_id();
  id.asset_data = BKE_asset_metadata_create();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  BKE_libblock_rename(*bmain_, id, "Personal", IDNewNameMode::RenameExistingNever);
  EXPECT_EQ(descriptor(id), nullptr);
  EXPECT_EQ(asset_descriptor(id), nullptr);
}

TEST_F(IDUINameTest, MalformedAssetRootIsPreservedWithoutUnsafeGroupAccess)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  id.asset_data = BKE_asset_metadata_create();
  id.asset_data->properties = idprop::create("unrelated", 42).release();
  BKE_id_ui_name_asset_sync(id);
  EXPECT_EQ(id.asset_data->properties->type, IDP_INT);
  EXPECT_EQ(IDP_int_get(id.asset_data->properties), 42);
  EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
}

TEST_F(IDUINameTest, WrongDescriptorTypeFallsBack)
{
  ID &id = new_id();
  id.system_properties = idprop::create_group("System").release();
  ASSERT_TRUE(
      IDP_AddToGroup(id.system_properties, idprop::create("_blender_ui_name", 1).release()));
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
}

TEST_F(IDUINameTest, UnsupportedVersionFallsBack)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  IDP_ReplaceInGroup(descriptor(id), idprop::create("version", 99).release());
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
}

TEST_F(IDUINameTest, WrongSourceTypeFallsBack)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  IDP_ReplaceInGroup(descriptor(id), idprop::create("source", 42).release());
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
}

TEST_F(IDUINameTest, MissingSourceFallsBack)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  IDP_FreeFromGroup(descriptor(id), source_property(id));
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
}

TEST_F(IDUINameTest, BinarySourceFallsBack)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  IDProperty *source = source_property(id);
  ASSERT_NE(source, nullptr);
  source->subtype = IDP_STRING_SUB_BYTE;
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
}

TEST_F(IDUINameTest, MissingSourceStorageFallsBack)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  IDProperty *source = source_property(id);
  ASSERT_NE(source, nullptr);
  void *storage = source->data.pointer;
  source->data.pointer = nullptr;
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
  source->data.pointer = storage;
}

TEST_F(IDUINameTest, MismatchedSourceFallsBackAndFinalizeRemovesNote)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  IDP_ReplaceInGroup(descriptor(id), IDP_NewString("Different", "source"));
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
  BKE_id_ui_name_copy_finalize(id);
  EXPECT_EQ(descriptor(id), nullptr);
}

TEST_F(IDUINameTest, DamagedSourceLengthsFallBackSafely)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  IDProperty *source = source_property(id);
  ASSERT_NE(source, nullptr);
  const int original_len = source->len;
  const int original_totallen = source->totallen;
  for (const int len : {-1, 0, 1, original_len + 1}) {
    source->len = len;
    EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
    EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
  }
  source->len = original_len;
  source->totallen = original_len - 1;
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  source->totallen = original_totallen;
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(id));
}

TEST_F(IDUINameTest, SourceMustIncludeItsTerminatingZero)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  IDProperty *source = source_property(id);
  ASSERT_NE(source, nullptr);
  char *text = static_cast<char *>(source->data.pointer);
  text[source->len - 1] = 'X';
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
  text[source->len - 1] = '\0';
}

TEST_F(IDUINameTest, MatchingInvalidUTF8SourceStillFallsBack)
{
  ID &id = new_id();
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  IDProperty *source = source_property(id);
  ASSERT_NE(source, nullptr);
  char *text = static_cast<char *>(source->data.pointer);
  /* Both strings match, but neither is valid text. Keep the ID allocated normally. */
  text[0] = char(0xff);
  id.name[2] = char(0xff);
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(BKE_id_ui_name_get(id), std::string(id.name + 2));
  text[0] = 'L';
  id.name[2] = 'L';
}

TEST_F(IDUINameTest, SearchUsesSourceWhenDisabledOrUnmarked)
{
  ID &id = new_id(ID_BR, "Smooth");
  EXPECT_EQ(BKE_id_ui_name_search_text(ID_BR, BKE_id_name(id), nullptr), "Smooth");
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  EXPECT_EQ(BKE_id_ui_name_search_text(ID_BR, BKE_id_name(id), id.system_properties), "Smooth");
  BKE_libblock_rename(*bmain_, id, "My brush");
  EXPECT_EQ(BKE_id_ui_name_search_text(ID_BR, BKE_id_name(id), id.system_properties), "My brush");
}

TEST_F(IDUINameTest, UserDuplicateClearsPermissionEvenInAnotherMain)
{
  ID &id = new_id(ID_BR, "Smooth");
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  Main *destination = BKE_main_new();
  ID *copy = BKE_id_copy_for_duplicate(destination, &id, USER_DUP_LINKED_ID, LIB_ID_COPY_DEFAULT);
  ASSERT_NE(copy, nullptr);
  EXPECT_STREQ(BKE_id_name(*copy), "Smooth");
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(*copy));
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(id));
  BKE_main_free(destination);
}

TEST_F(IDUINameTest, InternalReplacementKeepsOnlyMatchingExplicitPermission)
{
  ID &source = new_id(ID_BR, "Smooth");
  ASSERT_TRUE(BKE_id_ui_name_mark(source));
  Main *destination = BKE_main_new();
  ID &target = *static_cast<ID *>(BKE_id_new(destination, ID_BR, "Smooth"));
  BKE_id_ui_name_copy(target, source);
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(target));
  BKE_id_ui_name_clear(source);
  BKE_id_ui_name_copy(target, source);
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(target));
  ASSERT_TRUE(BKE_id_ui_name_mark(source));
  BKE_libblock_rename(*destination, target, "Personal");
  BKE_id_ui_name_copy(target, source);
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(target));
  BKE_main_free(destination);
}

TEST_F(IDUINameTest, RegistrationSnapshotCopiesOnlyTheValidAuthorNote)
{
  ID &id = new_id(ID_BR, "Smooth");
  EXPECT_EQ(BKE_id_ui_name_properties_copy(BKE_id_name(id), id.system_properties), nullptr);
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  IDP_ReplaceInGroup(id.system_properties, bke::idprop::create("unrelated", int32_t(7)).release());
  IDProperty *snapshot = BKE_id_ui_name_properties_copy(BKE_id_name(id), id.system_properties);
  ASSERT_NE(snapshot, nullptr);
  EXPECT_NE(IDP_GetPropertyFromGroup(snapshot, "_blender_ui_name"), nullptr);
  EXPECT_EQ(IDP_GetPropertyFromGroup(snapshot, "unrelated"), nullptr);
  EXPECT_EQ(BKE_id_ui_name_properties_copy("Renamed", id.system_properties), nullptr);
  IDP_FreeProperty(snapshot);
}

}  // namespace blender::bke::tests
