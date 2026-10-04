/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "AS_asset_library.hh"
#include "AS_asset_representation.hh"
#include "asset_library_service.hh"

#include "BKE_appdir.hh"
#include "BKE_asset.hh"
#include "BKE_context.hh"
#include "BKE_global.hh"
#include "BKE_gtest_base.hh"
#include "BKE_id_ui_name.hh"
#include "BKE_idprop.hh"
#include "BKE_lib_id.hh"
#include "BKE_main.hh"
#include "BKE_node.hh"
#include "BKE_preferences.h"
#include "BKE_wm_runtime.hh"

#include "BLI_fileops.hh"
#include "BLI_listbase.hh"
#include "BLI_path_utils.hh"
#include "BLI_string.hh"
#include "BLI_string_search.hh"

#include "BLO_writefile.hh"

#include "BLT_lang.hh"
#include "BLT_translation.hh"

#include "DNA_node_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"

#include "ED_asset_indexer.hh"
#include "ED_asset_list.hh"
#include "ED_asset_mark_clear.hh"
#include "ED_geometry.hh"
#include "RNA_access.hh"
#include "RNA_prototypes.hh"
#include "WM_api.hh"
#include "WM_types.hh"
#include "testing/testing.h"

#include "filelist.hh"

#include <fstream>
#include <iterator>

namespace blender::tests {

class OperatorDisplayNameTest : public bke::BlenderGTestBase {};

TEST_F(OperatorDisplayNameTest, ExistingCallbacksRequireProperties)
{
  wmOperatorType type;
  type.srna = RNA_Operator;
  type.get_name = [](wmOperatorType *, PointerRNA *properties) {
    EXPECT_NE(properties, nullptr);
    return std::string("Property-dependent label");
  };
  EXPECT_TRUE(type.name_requires_properties);
  EXPECT_EQ(WM_operatortype_name(&type, nullptr), RNA_struct_ui_name(RNA_Operator));
  PointerRNA properties;
  EXPECT_EQ(WM_operatortype_name(&type, &properties), "Property-dependent label");
}

TEST_F(OperatorDisplayNameTest, IndependentCallbacksWorkWithoutProperties)
{
  wmOperatorType type;
  type.srna = RNA_Operator;
  type.name_requires_properties = false;
  type.get_name = [](wmOperatorType *, PointerRNA *properties) {
    EXPECT_EQ(properties, nullptr);
    return std::string("Resolved tool label");
  };
  EXPECT_EQ(WM_operatortype_name(&type, nullptr), "Resolved tool label");
}

TEST_F(OperatorDisplayNameTest, EmptyCallbackKeepsExistingFallback)
{
  wmOperatorType type;
  type.srna = RNA_Operator;
  type.name_requires_properties = false;
  type.get_name = [](wmOperatorType *, PointerRNA *) { return std::string(); };
  EXPECT_EQ(WM_operatortype_name(&type, nullptr), RNA_struct_ui_name(RNA_Operator));
}

class RegisteredNodeToolDisplayNameTest : public bke::BlenderGTestBase {
 protected:
  Main *main_ = nullptr;
  Main *previous_main_ = nullptr;
  bContext *context_ = nullptr;
  wmWindowManager manager_;
  std::unique_ptr<bke::WindowManagerRuntime> manager_runtime_;
  bNodeTree *group_ = nullptr;
  std::string previous_locale_;
  eUserpref_Translation_Flags previous_translation_flags_;
  std::string temporary_library_path_;
  bUserAssetLibrary *temporary_library_ = nullptr;

  void SetUp() override
  {
    previous_main_ = G_MAIN;
    main_ = BKE_main_new();
    G_MAIN = main_;
    context_ = CTX_create();
    manager_runtime_ = std::make_unique<bke::WindowManagerRuntime>();
    manager_.runtime = manager_runtime_.get();
    CTX_data_main_set(context_, main_);
    CTX_wm_manager_set(context_, &manager_);
    previous_locale_ = BLT_lang_get();
    previous_translation_flags_ = U.transopts;

    /* Round has a real NodeTree-context Vietnamese catalogue entry. */
    group_ = bke::node_tree_add_tree(main_, "Round", "GeometryNodeTree");
    group_->geometry_node_asset_traits = MEM_new<GeometryNodeAssetTraits>(__func__);
    group_->geometry_node_asset_traits->flag = GEO_NODE_ASSET_TOOL;
    group_->geometry_node_asset_traits->node_tool_idname = BLI_strdup("geometry.review_ui_name");
    /* Load through the ordinary asset-list API before registration, so tests need no UI window
     * or background reading job. */
    ed::asset::list::storage_fetch_blocking(asset_system::all_library_reference(), *context_);
  }

  void TearDown() override
  {
    group_->geometry_node_asset_traits->flag &= ~GEO_NODE_ASSET_TOOL;
    /* The fixture may have registered bundled tools as well. Clear the tool trait only in these
     * temporary metadata copies, so ordinary registration frees every generated RNA type before
     * the test suite shuts down RNA. No library files or linked IDs are modified. */
    ed::asset::list::iterate(asset_system::all_library_reference(), [&](auto &asset) {
      IDProperty *traits = BKE_asset_metadata_idprop_find(&asset.get_metadata(),
                                                          "geometry_node_asset_traits_flag");
      const bool has_tool_traits = traits && traits->type == IDP_INT;
      if (has_tool_traits) {
        IDP_int_set(traits, IDP_int_get(traits) & ~GEO_NODE_ASSET_TOOL);
      }
      return true;
    });
    ed::geometry::register_node_group_operators(*context_);
    EXPECT_EQ(WM_operatortype_find("GEOMETRY_OT_review_ui_name", true), nullptr);
    for (const wmOperatorType *type : WM_operatortypes_registered_get()) {
      EXPECT_EQ(type->flag & OPTYPE_NODE_TOOL, 0);
    }
    ed::asset::list::storage_exit();
    asset_system::AssetLibraryService::destroy();
    const bool has_temporary_library = temporary_library_ != nullptr;
    if (has_temporary_library) {
      BKE_preferences_asset_library_remove(&U, temporary_library_);
    }
    const bool has_temporary_directory = !temporary_library_path_.empty();
    if (has_temporary_directory) {
      EXPECT_EQ(BLI_delete(temporary_library_path_.c_str(), true, true), 0);
    }
    CTX_free(context_);
    BKE_main_free(main_);
    G_MAIN = previous_main_;
    U.transopts = previous_translation_flags_;
    BLT_lang_set(previous_locale_.c_str());
  }
};

TEST_F(RegisteredNodeToolDisplayNameTest, MarkedToolLocaleToggleAndRename)
{
  const bool has_translation_support = BLT_translate();
  if (!has_translation_support) {
    GTEST_SKIP() << "Requires an international build";
  }
  ASSERT_TRUE(BKE_id_ui_name_mark(group_->id));
  BLT_lang_set("vi_VN");
  U.transopts |= USER_TR_IFACE;
  ed::geometry::register_node_group_operators(*context_);
  wmOperatorType *type = WM_operatortype_find("GEOMETRY_OT_review_ui_name", true);
  ASSERT_NE(type, nullptr);
  EXPECT_FALSE(type->name_requires_properties);
  EXPECT_STREQ(type->name, "Round");
  const std::string translated = WM_operatortype_name(type, nullptr);
  ASSERT_NE(translated, "Round");
  EXPECT_EQ(translated, std::string(BKE_id_ui_name_get(group_->id)));
  EXPECT_STREQ(group_->id.name + 2, "Round");
  EXPECT_TRUE(main_->libraries.is_empty());
  EXPECT_EQ(main_->nodetrees.count(), 1);

  U.transopts &= ~USER_TR_IFACE;
  EXPECT_EQ(WM_operatortype_name(type, nullptr), "Round");
  U.transopts |= USER_TR_IFACE;
  EXPECT_EQ(WM_operatortype_name(type, nullptr), translated);

  BKE_id_ui_name_clear(group_->id);
  ed::geometry::register_node_group_operators(*context_);
  type = WM_operatortype_find("GEOMETRY_OT_review_ui_name", true);
  ASSERT_NE(type, nullptr);
  EXPECT_EQ(WM_operatortype_name(type, nullptr), "Round");
  ASSERT_TRUE(BKE_id_ui_name_mark(group_->id));
  ed::geometry::register_node_group_operators(*context_);
  type = WM_operatortype_find("GEOMETRY_OT_review_ui_name", true);
  ASSERT_NE(type, nullptr);
  EXPECT_EQ(WM_operatortype_name(type, nullptr), translated);

  BKE_id_rename(*main_, group_->id, "My literal node tool");
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(group_->id));
  /* The normal ID notifier refreshes the existing registration and its name snapshot. */
  ed::geometry::register_node_group_operators(*context_);
  type = WM_operatortype_find("GEOMETRY_OT_review_ui_name", true);
  ASSERT_NE(type, nullptr);
  EXPECT_STREQ(type->name, "My literal node tool");
  EXPECT_EQ(WM_operatortype_name(type, nullptr), "My literal node tool");
  EXPECT_TRUE(main_->libraries.is_empty());
  EXPECT_EQ(main_->nodetrees.count(), 1);
}

TEST_F(RegisteredNodeToolDisplayNameTest, SavedExternalBrushAssetScanAndSearch)
{
  const bool has_translation_support = BLT_translate();
  if (!has_translation_support) {
    GTEST_SKIP() << "Requires an international build";
  }
  BKE_tempdir_init(nullptr);
  temporary_library_path_ = std::string(BKE_tempdir_session()) + "external-ui-name-review";
  ASSERT_TRUE(BLI_dir_create_recursive(temporary_library_path_.c_str()));
  char filepath[FILE_MAX];
  BLI_path_join(filepath, sizeof(filepath), temporary_library_path_.c_str(), "marked.blend");

  /* Write actual authored data, then discard it before asking the browser to scan the file. */
  std::unique_ptr<Main, decltype(&BKE_main_free)> author_main(BKE_main_new(), BKE_main_free);
  ID &brush = *static_cast<ID *>(BKE_id_new(author_main.get(), ID_BR, "Smooth"));
  ASSERT_TRUE(ed::asset::mark_id(&brush));
  ASSERT_TRUE(BKE_id_ui_name_mark(brush));
  BlendFileWriteParams write_params{};
  ASSERT_TRUE(BLO_write_file(author_main.get(), filepath, 0, &write_params, nullptr));
  author_main.reset();
  ASSERT_TRUE(main_->brushes.is_empty());
  ASSERT_TRUE(main_->libraries.is_empty());

  auto read_bytes = [&]() {
    std::ifstream stream(filepath, std::ios::binary);
    EXPECT_TRUE(stream.good());
    return std::string(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
  };
  const std::string saved_bytes = read_bytes();
  ASSERT_FALSE(saved_bytes.empty());
  temporary_library_ = BKE_preferences_asset_library_add(
      &U, "External UI name test", temporary_library_path_.c_str());
  ASSERT_NE(temporary_library_, nullptr);
  AssetLibraryReference library_ref{};
  library_ref.type = ASSET_LIBRARY_CUSTOM;
  library_ref.custom_library_index = BKE_preferences_asset_library_get_index(&U,
                                                                             temporary_library_);
  ed::asset::list::storage_fetch_blocking(library_ref, *context_);

  asset_system::AssetRepresentation *asset = nullptr;
  int asset_count = 0;
  ed::asset::list::iterate(library_ref, [&](auto &entry) {
    asset = &entry;
    asset_count++;
    return true;
  });
  ASSERT_EQ(asset_count, 1);
  ASSERT_NE(asset, nullptr);
  EXPECT_EQ(asset->local_id(), nullptr);
  EXPECT_EQ(asset->get_name(), "Smooth");
  const std::string relative_identifier = asset->library_relative_identifier();
  EXPECT_EQ(relative_identifier, "marked.blend" SEP_STR "Brush" SEP_STR "Smooth");
  const AssetWeakReference weak_reference = asset->make_weak_reference();
  const std::string source_reference = weak_reference.relative_asset_identifier;
  std::unique_ptr<IDProperty, bke::idprop::IDPropertyDeleter> scanned_note(
      BKE_id_ui_name_properties_copy(asset->get_name(), asset->get_metadata().properties));
  ASSERT_NE(scanned_note, nullptr);

  BLT_lang_set("vi_VN");
  U.transopts |= USER_TR_IFACE;
  const std::string translated = asset->get_display_name();
  ASSERT_NE(translated, "Smooth");
  auto search_for = [&](StringRef query) {
    string_search::StringSearch<asset_system::AssetRepresentation> search(
        nullptr, string_search::MainWordsHeuristic::All);
    search.add(
        BKE_id_ui_name_search_text(ID_BR, asset->get_name(), asset->get_metadata().properties),
        asset);
    return search.query(query);
  };
  const Vector<asset_system::AssetRepresentation *> source_matches = search_for("Smooth");
  const Vector<asset_system::AssetRepresentation *> translated_matches = search_for(translated);
  ASSERT_EQ(source_matches.size(), 1);
  ASSERT_EQ(translated_matches.size(), 1);
  EXPECT_EQ(source_matches[0], asset);
  EXPECT_EQ(translated_matches[0], asset);

  U.transopts &= ~USER_TR_IFACE;
  EXPECT_EQ(asset->get_display_name(), "Smooth");
  EXPECT_EQ(search_for("Smooth").size(), 1);
  EXPECT_TRUE(search_for(translated).is_empty());
  U.transopts |= USER_TR_IFACE;
  BLT_lang_set("en_US");
  EXPECT_EQ(asset->get_display_name(), "Smooth");
  EXPECT_EQ(asset->library_relative_identifier(), relative_identifier);
  const AssetWeakReference current_reference = asset->make_weak_reference();
  EXPECT_EQ(std::string(current_reference.relative_asset_identifier), source_reference);
  EXPECT_TRUE(main_->brushes.is_empty());
  EXPECT_TRUE(main_->libraries.is_empty());
  EXPECT_EQ(read_bytes(), saved_bytes);
}

TEST_F(RegisteredNodeToolDisplayNameTest, ExternalFileListColdAndWarmTranslatedSearch)
{
  const bool has_translation_support = BLT_translate();
  if (!has_translation_support) {
    GTEST_SKIP() << "Requires an international build";
  }
  BKE_tempdir_init(nullptr);
  temporary_library_path_ = std::string(BKE_tempdir_session()) + "external-ui-name-filelist";
  ASSERT_TRUE(BLI_dir_create_recursive(temporary_library_path_.c_str()));
  char filepath[FILE_MAX];
  BLI_path_join(filepath, sizeof(filepath), temporary_library_path_.c_str(), "marked.blend");
  std::unique_ptr<Main, decltype(&BKE_main_free)> author_main(BKE_main_new(), BKE_main_free);
  ID &brush = *static_cast<ID *>(BKE_id_new(author_main.get(), ID_BR, "Smooth"));
  ASSERT_TRUE(ed::asset::mark_id(&brush));
  ASSERT_TRUE(BKE_id_ui_name_mark(brush));
  BlendFileWriteParams write_params{};
  ASSERT_TRUE(BLO_write_file(author_main.get(), filepath, 0, &write_params, nullptr));
  author_main.reset();
  auto read_bytes = [&]() {
    std::ifstream stream(filepath, std::ios::binary);
    EXPECT_TRUE(stream.good());
    return std::string(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
  };
  const std::string saved_bytes = read_bytes();
  ASSERT_FALSE(saved_bytes.empty());
  temporary_library_ = BKE_preferences_asset_library_add(
      &U, "External FileList test", temporary_library_path_.c_str());
  ASSERT_NE(temporary_library_, nullptr);
  AssetLibraryReference library_ref{};
  library_ref.type = ASSET_LIBRARY_CUSTOM;
  library_ref.custom_library_index = BKE_preferences_asset_library_get_index(&U,
                                                                             temporary_library_);

  /* Blocking scans make these callback counters local to this serial test. Every operation,
   * including initialization, writing and cleanup, still uses the real disk indexer. */
  static int index_hits;
  static int index_misses;
  FileIndexerType counted_indexer = ed::asset::index::file_indexer_asset;
  counted_indexer.read_index = [](const char *filename,
                                 FileIndexerEntries *entries,
                                 int *entries_num,
                                 void *user_data) {
    const eFileIndexerResult result = ed::asset::index::file_indexer_asset.read_index(
        filename, entries, entries_num, user_data);
    index_hits += result == FILE_INDEXER_ENTRIES_LOADED;
    index_misses += result == FILE_INDEXER_NEEDS_UPDATE;
    return result;
  };

  for (const bool warm_cache : {false, true}) {
    SCOPED_TRACE(warm_cache ? "Warm disk index" : "Cold blend-file scan");
    index_hits = index_misses = 0;
    std::unique_ptr<FileList, decltype(&filelist_free)> files(
        filelist_new(FILE_ASSET_LIBRARY, false), filelist_free);
    filelist_setlibrary(files.get(), &library_ref);
    filelist_setsorting(files.get(), FILE_SORT_ALPHA, false);
    filelist_setrecursion(files.get(), FILE_SELECT_MAX_RECURSIONS);
    filelist_setindexer(files.get(), &counted_indexer);
    char directory[FILE_MAX_LIBEXTRA];
    STRNCPY(directory, temporary_library_path_.c_str());
    filelist_setdir(files.get(), directory);
    auto set_query = [&](const char *query) {
      filelist_setfilter_options(files.get(),
                                 true,
                                 true,
                                 true,
                                 FILE_TYPE_BLENDERLIB,
                                 FILTER_ID_BR,
                                 true,
                                 false,
                                 false,
                                 query);
    };
    auto filter_for = [&](const char *query) {
      set_query(query);
      return filelist_files_ensure(files.get());
    };
    set_query("");
    filelist_readjob_blocking_run(files.get(), NC_SPACE | ND_SPACE_FILE_LIST, context_);
    EXPECT_EQ(index_hits, int(warm_cache));
    EXPECT_EQ(index_misses, int(!warm_cache));
    ASSERT_EQ(filter_for(""), 1);
    /* Browser drawing allocates its visible-entry cache before requesting a FileDirEntry. */
    filelist_file_cache_slidingwindow_set(files.get(), 1);
    FileDirEntry *entry = filelist_file(files.get(), 0);
    ASSERT_NE(entry, nullptr);
    asset_system::AssetRepresentation *asset = entry->asset;
    ASSERT_NE(asset, nullptr);
    ASSERT_EQ(asset->local_id(), nullptr);
    ASSERT_EQ(asset->get_name(), "Smooth");
    const std::string relative_path = entry->relpath;
    EXPECT_EQ(relative_path, "marked.blend" SEP_STR "Brush" SEP_STR "Smooth");
    const AssetWeakReference weak_reference = asset->make_weak_reference();
    const std::string source_reference = weak_reference.relative_asset_identifier;

    BLT_lang_set("vi_VN");
    U.transopts |= USER_TR_IFACE;
    const std::string translated = asset->get_display_name();
    ASSERT_NE(translated, "Smooth");
    ASSERT_EQ(filter_for("Smooth"), 1);
    EXPECT_EQ(filelist_entry_get_asset_representation(files.get(), 0), asset);
    ASSERT_EQ(filter_for(translated.c_str()), 1);
    EXPECT_EQ(filelist_entry_get_asset_representation(files.get(), 0), asset);

    /* The active query remains unchanged. This explicit tag tests cached FileList refiltering,
     * not notifier delivery to an external browser. */
    U.transopts &= ~USER_TR_IFACE;
    filelist_tag_needs_filtering(files.get());
    EXPECT_EQ(filelist_files_ensure(files.get()), 0);
    EXPECT_EQ(asset->get_display_name(), "Smooth");
    U.transopts |= USER_TR_IFACE;
    filelist_tag_needs_filtering(files.get());
    ASSERT_EQ(filelist_files_ensure(files.get()), 1);
    EXPECT_EQ(filelist_entry_get_asset_representation(files.get(), 0), asset);
    EXPECT_EQ(filelist_entry_get_relpath(files.get(), 0), relative_path);
    BLT_lang_set("en_US");
    filelist_tag_needs_filtering(files.get());
    EXPECT_EQ(filelist_files_ensure(files.get()), 0);
    ASSERT_EQ(filter_for("Smooth"), 1);
    EXPECT_EQ(filelist_file(files.get(), 0)->asset, asset);
    EXPECT_EQ(asset->get_display_name(), "Smooth");
    const AssetWeakReference current_reference = asset->make_weak_reference();
    EXPECT_EQ(std::string(current_reference.relative_asset_identifier), source_reference);
    EXPECT_TRUE(main_->brushes.is_empty());
    EXPECT_TRUE(main_->libraries.is_empty());
    EXPECT_EQ(read_bytes(), saved_bytes);
  }
}

}  // namespace blender::tests
