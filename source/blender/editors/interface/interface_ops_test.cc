/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_action.hh"
#include "BKE_context.hh"
#include "BKE_anim_data.hh"
#include "BKE_fcurve.hh"
#include "BKE_gtest_base.hh"
#include "BKE_idtype.hh"
#include "BKE_id_ui_name.hh"
#include "BKE_global.hh"
#include "BKE_lib_id.hh"
#include "BKE_main.hh"
#include "BKE_object.hh"

#include "DNA_anim_types.h"
#include "DNA_windowmanager_types.h"
#include "DNA_userdef_types.h"

#include "BLT_lang.hh"
#include "BLT_translation.hh"
#include "BLO_userdef_default.h"
#include "BLI_string.hh"
#include "MEM_guardedalloc.h"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_prototypes.hh"

#include "BLI_listbase.hh"
#include "BLI_string_utf8.hh"

#include "ED_keyframing.hh"

#include "ANIM_action.hh"
#include "ANIM_animdata.hh"
#include "ANIM_fcurve.hh"

#include "interface_intern.hh"

#include "testing/testing.h"

#include <cmath>

namespace blender::ui::tests {

class IDNameEditTest : public bke::BlenderGTestBase {
 protected:
  Main *main_ = nullptr;
  Main *previous_main_ = nullptr;
  bContext *context_ = nullptr;
  std::string previous_locale_;
  eUserpref_Translation_Flags previous_flags_;

  void SetUp() override
  {
    main_ = BKE_main_new();
    previous_main_ = G_MAIN;
    G_MAIN = main_;
    context_ = CTX_create();
    CTX_data_main_set(context_, main_);
    previous_locale_ = BLT_lang_get();
    previous_flags_ = U.transopts;
    BLT_lang_set("vi_VN");
    U.transopts |= USER_TR_IFACE;
  }

  void TearDown() override
  {
    CTX_free(context_);
    G_MAIN = previous_main_;
    BKE_main_free(main_);
    U.transopts = previous_flags_;
    BLT_lang_set(previous_locale_.c_str());
  }
};

TEST_F(IDNameEditTest, EligibleRNANameStartsInSelectedLanguage)
{
#ifndef WITH_INTERNATIONAL
  GTEST_SKIP() << "Blender was built without translations";
#endif
  ID &id = *static_cast<ID *>(BKE_id_new(main_, ID_WS, "Layout"));
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  const std::string translated = BKE_id_ui_name_get(id);
  ASSERT_NE(translated, "Layout");
  ButtonText button;
  button.type = ButtonType::Text;
  button.rnapoin = RNA_id_pointer_create(&id);
  button.rnaprop = RNA_struct_name_property(button.rnapoin.type);
  int capacity = 7;
  char *text = MEM_new_array<char>(capacity, __func__);
  button_string_get(&button, text, capacity);
  EXPECT_STREQ(text, "Layout");
  const auto snapshot = button_id_name_edit_begin(button, text, capacity);
  EXPECT_TRUE(snapshot.has_value());
  EXPECT_GE(capacity, translated.size() + 1);
  EXPECT_STREQ(text, translated.c_str());
  EXPECT_STREQ(id.name + 2, "Layout");
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(id));
  MEM_delete(text);
}

TEST_F(IDNameEditTest, UnchangedAndCanceledEditsPreserveSourceAndNote)
{
#ifndef WITH_INTERNATIONAL
  GTEST_SKIP() << "Blender was built without translations";
#endif
  ID &id = *static_cast<ID *>(BKE_id_new(main_, ID_WS, "Layout"));
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  const std::string display = BKE_id_ui_name_get(id);
  ASSERT_NE(display, "Layout");
  const ButtonIDNameEdit snapshot{&id, display};
  EXPECT_EQ(button_id_name_edit_apply(snapshot, display, "Layout", false), "Layout");
  EXPECT_EQ(button_id_name_edit_apply(snapshot, "Typed name", "Layout", true), "Layout");
  EXPECT_EQ(button_id_name_edit_apply(snapshot, "Layout", "Layout", true), "Layout");
  /* apply_but() transfers original_string into edit_string before a canceled apply. */
  EXPECT_EQ(button_id_name_edit_apply(snapshot, "Layout", nullptr, true), "Layout");
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(id));
  /* Confirmation uses the captured display, even after the locale has changed. */
  BLT_lang_set("en_US");
  EXPECT_EQ(button_id_name_edit_apply(snapshot, display, "Layout", false), "Layout");
  EXPECT_STREQ(id.name + 2, "Layout");
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(id));
}

TEST_F(IDNameEditTest, DeliberateSourceTextBecomesLiteral)
{
#ifndef WITH_INTERNATIONAL
  GTEST_SKIP() << "Blender was built without translations";
#endif
  ID &id = *static_cast<ID *>(BKE_id_new(main_, ID_WS, "Layout"));
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  const std::string display = BKE_id_ui_name_get(id);
  ASSERT_NE(display, "Layout");
  const ButtonIDNameEdit snapshot{&id, display};
  EXPECT_EQ(button_id_name_edit_apply(snapshot, "Layout", "Layout", false), "Layout");
  EXPECT_STREQ(id.name + 2, "Layout");
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_EQ(BKE_id_ui_name_get(id), "Layout");
}

TEST_F(IDNameEditTest, ChangedTextUsesExistingRNANameSetter)
{
#ifndef WITH_INTERNATIONAL
  GTEST_SKIP() << "Blender was built without translations";
#endif
  ID &id = *static_cast<ID *>(BKE_id_new(main_, ID_WS, "Layout"));
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  const std::string display = BKE_id_ui_name_get(id);
  ASSERT_NE(display, "Layout");
  const ButtonIDNameEdit snapshot{&id, display};
  ButtonText button;
  button.type = ButtonType::Text;
  button.rnapoin = RNA_id_pointer_create(&id);
  button.rnaprop = RNA_struct_name_property(button.rnapoin.type);
  const StringRefNull unchanged = button_id_name_edit_apply(snapshot, display, "Layout", false);
  EXPECT_TRUE(button_string_set(context_, &button, unchanged.c_str()));
  EXPECT_STREQ(id.name + 2, "Layout");
  EXPECT_TRUE(BKE_id_ui_name_is_translatable(id));
  const StringRefNull changed = button_id_name_edit_apply(
      snapshot, "Tên của tôi", "Layout", false);
  EXPECT_TRUE(button_string_set(context_, &button, changed.c_str()));
  EXPECT_STREQ(id.name + 2, "Tên của tôi");
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
  EXPECT_TRUE(button_string_set(context_, &button, "Layout"));
  EXPECT_FALSE(BKE_id_ui_name_is_translatable(id));
}

TEST_F(IDNameEditTest, TabAndExplicitOutlinerOwnerUseTheSameEditStart)
{
#ifndef WITH_INTERNATIONAL
  GTEST_SKIP() << "Blender was built without translations";
#endif
  ID &id = *static_cast<ID *>(BKE_id_new(main_, ID_WS, "Layout"));
  ASSERT_TRUE(BKE_id_ui_name_mark(id));
  const std::string display = BKE_id_ui_name_get(id);
  ASSERT_NE(display, "Layout");
  /* The active workspace pointer belongs to Window, while the tab represents this ID. */
  wmWindow window{};
  ButtonTab tab;
  tab.type = ButtonType::Tab;
  tab.rnapoin = RNA_pointer_create_discrete(nullptr, RNA_Window, &window);
  tab.rnaprop = RNA_struct_find_property(&tab.rnapoin, "workspace");
  tab.custom_data = &id;
  int capacity = 7;
  char *text = MEM_new_array<char>(capacity, __func__);
  button_string_get(&tab, text, capacity);
  EXPECT_STREQ(text, "Layout");
  EXPECT_TRUE(button_id_name_edit_begin(tab, text, capacity).has_value());
  EXPECT_STREQ(text, display.c_str());
  MEM_delete(text);

  ButtonText outliner;
  outliner.type = ButtonType::Text;
  text_button_id_name_set(&outliner, &id);
  text = BLI_strdup("Layout");
  capacity = 7;
  EXPECT_TRUE(button_id_name_edit_begin(outliner, text, capacity).has_value());
  EXPECT_STREQ(text, display.c_str());
  MEM_delete(text);
}

TEST_F(IDNameEditTest, LiteralNamesAndPointerSelectionKeepExistingBehavior)
{
  ID &id = *static_cast<ID *>(BKE_id_new(main_, ID_WS, "Layout"));
  ButtonText button;
  button.type = ButtonType::Text;
  button.rnapoin = RNA_id_pointer_create(&id);
  button.rnaprop = RNA_struct_name_property(button.rnapoin.type);
  int capacity = 7;
  char *text = BLI_strdup("Layout");
  EXPECT_FALSE(button_id_name_edit_begin(button, text, capacity).has_value());
  EXPECT_STREQ(text, "Layout");
  EXPECT_TRUE(BKE_id_ui_name_mark(id));
  U.transopts &= ~USER_TR_IFACE;
  EXPECT_FALSE(button_id_name_edit_begin(button, text, capacity).has_value());
  EXPECT_STREQ(text, "Layout");
  U.transopts |= USER_TR_IFACE;

  wmWindow window{};
  ButtonSearch selector;
  selector.type = ButtonType::SearchMenu;
  selector.rnapoin = RNA_pointer_create_discrete(nullptr, RNA_Window, &window);
  selector.rnaprop = RNA_struct_find_property(&selector.rnapoin, "workspace");
  selector.custom_data = &id;
  EXPECT_FALSE(button_id_name_edit_begin(selector, text, capacity).has_value());
  EXPECT_STREQ(text, "Layout");
  MEM_delete(text);
}

TEST_F(IDNameEditTest, TabTextSelectionContrastsWithBothTabBackgrounds)
{
  const ThemeUI &theme = U_theme_default.tui;
  uchar tab_selection[4];
  widget_text_selection_color(&theme.wcol_tab, &theme, ButtonType::Tab, tab_selection);
  EXPECT_EQ(tab_selection[3], 51);
  for (const uchar *background : {theme.wcol_tab.inner, theme.wcol_tab.inner_sel}) {
    for (int channel = 0; channel < 3; channel++) {
      const float alpha = tab_selection[3] / 255.0f;
      const float contrast = std::abs((tab_selection[channel] - background[channel]) * alpha);
      /* Normal text selection has more than 40 levels of contrast in this same default theme. */
      EXPECT_GE(contrast, 30.0f);
    }
  }
  uchar text_selection[4];
  widget_text_selection_color(&theme.wcol_text, nullptr, ButtonType::Text, text_selection);
  for (int channel = 0; channel < 3; channel++) {
    EXPECT_EQ(text_selection[channel], theme.wcol_text.item[channel]);
  }
  EXPECT_EQ(text_selection[3], 51);
}

class CopyDriversToSelected : public bke::BlenderGTestBase {
 public:
  Main *bmain;

  Object *cube;
  Object *suzanne;

  PointerRNA cube_ptr;
  PropertyRNA *cube_quaternion_prop;
  PropertyRNA *cube_rotation_mode_prop;

  PointerRNA suzanne_ptr;
  PropertyRNA *suzanne_quaternion_prop;
  PropertyRNA *suzanne_rotation_mode_prop;

  void SetUp() override
  {
    bmain = BKE_main_new();

    cube = BKE_object_add_only_object(bmain, OB_EMPTY, "OBCube");
    suzanne = BKE_object_add_only_object(bmain, OB_EMPTY, "OBSuzanne");

    cube_ptr = RNA_pointer_create_discrete(&cube->id, RNA_Object, &cube->id);
    cube_quaternion_prop = RNA_struct_find_property(&cube_ptr, "rotation_quaternion");
    cube_rotation_mode_prop = RNA_struct_find_property(&cube_ptr, "rotation_mode");

    suzanne_ptr = RNA_pointer_create_discrete(&suzanne->id, RNA_Object, &suzanne->id);
    suzanne_quaternion_prop = RNA_struct_find_property(&suzanne_ptr, "rotation_quaternion");
    suzanne_rotation_mode_prop = RNA_struct_find_property(&suzanne_ptr, "rotation_mode");

    AnimData *adt_cube = BKE_animdata_ensure_id(&cube->id);
    AnimData *adt_suzanne = BKE_animdata_ensure_id(&suzanne->id);

    ReportList tmp_report_list;

    /* Set up cube drivers. */
    ANIM_add_driver(&tmp_report_list, &cube->id, "rotation_quaternion", 0, 0, DRIVER_TYPE_PYTHON);
    ANIM_add_driver(&tmp_report_list, &cube->id, "rotation_quaternion", 1, 0, DRIVER_TYPE_PYTHON);
    FCurve *cube_quat_0_driver = static_cast<FCurve *>(BLI_findlink(&adt_cube->drivers, 0));
    FCurve *cube_quat_1_driver = static_cast<FCurve *>(BLI_findlink(&adt_cube->drivers, 1));
    STRNCPY_UTF8(cube_quat_0_driver->driver->expression, "0.0");
    STRNCPY_UTF8(cube_quat_1_driver->driver->expression, "1.0");

    /* Set up suzanne drivers. */
    ANIM_add_driver(
        &tmp_report_list, &suzanne->id, "rotation_quaternion", 0, 0, DRIVER_TYPE_PYTHON);
    ANIM_add_driver(
        &tmp_report_list, &suzanne->id, "rotation_quaternion", 2, 0, DRIVER_TYPE_PYTHON);
    ANIM_add_driver(
        &tmp_report_list, &suzanne->id, "rotation_quaternion", 3, 0, DRIVER_TYPE_PYTHON);
    ANIM_add_driver(&tmp_report_list, &suzanne->id, "rotation_mode", 0, 0, DRIVER_TYPE_PYTHON);
    FCurve *suzanne_quat_0_driver = static_cast<FCurve *>(BLI_findlink(&adt_suzanne->drivers, 0));
    FCurve *suzanne_quat_2_driver = static_cast<FCurve *>(BLI_findlink(&adt_suzanne->drivers, 1));
    FCurve *suzanne_quat_3_driver = static_cast<FCurve *>(BLI_findlink(&adt_suzanne->drivers, 2));
    FCurve *suzanne_rotation_mode_driver = static_cast<FCurve *>(
        BLI_findlink(&adt_suzanne->drivers, 3));
    STRNCPY_UTF8(suzanne_quat_0_driver->driver->expression, "0.5");
    STRNCPY_UTF8(suzanne_quat_2_driver->driver->expression, "2.5");
    STRNCPY_UTF8(suzanne_quat_3_driver->driver->expression, "3.5");
    STRNCPY_UTF8(suzanne_rotation_mode_driver->driver->expression, "4");

    /* Add animation to cube's fourth quaternion element. */
    PointerRNA cube_ptr = RNA_pointer_create_discrete(&cube->id, RNA_Object, &cube->id);
    bAction *act = animrig::id_action_ensure(bmain, &cube->id);
    FCurve *fcu = animrig::action_fcurve_ensure_ex(
        bmain, act, &cube_ptr, {"rotation_quaternion", 3});
    animrig::KeyframeSettings keyframe_settings = {BEZT_KEYTYPE_KEYFRAME, HD_AUTO, BEZT_IPO_BEZ};
    insert_vert_fcurve(fcu, {1.0, 1.0}, keyframe_settings, INSERTKEY_NOFLAGS);
  }

  void TearDown() override
  {
    BKE_main_free(bmain);
    RNA_exit();
  }
};

TEST_F(CopyDriversToSelected, get_property_drivers)
{
  /* Cube quaternion: get all drivers. */
  {
    bool is_array_prop;
    Vector<FCurve *> drivers = internal::get_property_drivers(
        &cube_ptr, cube_quaternion_prop, true, -1, &is_array_prop);

    EXPECT_EQ(is_array_prop, true);
    EXPECT_EQ(drivers.size(), 4);

    EXPECT_NE(drivers[0], nullptr);
    EXPECT_NE(drivers[1], nullptr);
    EXPECT_EQ(drivers[2], nullptr);
    EXPECT_EQ(drivers[3], nullptr);

    EXPECT_STREQ(drivers[0]->driver->expression, "0.0");
    EXPECT_STREQ(drivers[1]->driver->expression, "1.0");
  }

  /* Cube quaternion: get first element driver. */
  {
    bool is_array_prop;
    Vector<FCurve *> drivers = internal::get_property_drivers(
        &cube_ptr, cube_quaternion_prop, false, 0, &is_array_prop);

    EXPECT_EQ(is_array_prop, true);
    EXPECT_EQ(drivers.size(), 4);

    EXPECT_NE(drivers[0], nullptr);
    EXPECT_EQ(drivers[1], nullptr);
    EXPECT_EQ(drivers[2], nullptr);
    EXPECT_EQ(drivers[3], nullptr);

    EXPECT_STREQ(drivers[0]->driver->expression, "0.0");
  }

  /* Cube quaternion: try to get fourth element driver. Since there is none, we
   * should get back an empty vector, indicating that no drivers were found. */
  {
    bool is_array_prop;
    Vector<FCurve *> drivers = internal::get_property_drivers(
        &cube_ptr, cube_quaternion_prop, false, 3, &is_array_prop);

    EXPECT_EQ(drivers.size(), 0);
  }

  /* Cube rotation mode: get driver. Since there is none, we should get back an
   * empty vector, indicating that no drivers were found. */
  {
    bool is_array_prop;
    Vector<FCurve *> drivers = internal::get_property_drivers(
        &cube_ptr, cube_rotation_mode_prop, false, 0, &is_array_prop);

    EXPECT_EQ(drivers.size(), 0);
  }

  /* Suzanne quaternion: get all drivers. */
  {
    bool is_array_prop;
    Vector<FCurve *> drivers = internal::get_property_drivers(
        &suzanne_ptr, suzanne_quaternion_prop, true, -1, &is_array_prop);

    EXPECT_EQ(is_array_prop, true);
    EXPECT_EQ(drivers.size(), 4);

    EXPECT_NE(drivers[0], nullptr);
    EXPECT_EQ(drivers[1], nullptr);
    EXPECT_NE(drivers[2], nullptr);
    EXPECT_NE(drivers[3], nullptr);

    EXPECT_STREQ(drivers[0]->driver->expression, "0.5");
    EXPECT_STREQ(drivers[2]->driver->expression, "2.5");
    EXPECT_STREQ(drivers[3]->driver->expression, "3.5");
  }

  /* Suzanne quaternion: get first element driver. */
  {
    bool is_array_prop;
    Vector<FCurve *> drivers = internal::get_property_drivers(
        &suzanne_ptr, suzanne_quaternion_prop, false, 0, &is_array_prop);

    EXPECT_EQ(is_array_prop, true);
    EXPECT_EQ(drivers.size(), 4);

    EXPECT_NE(drivers[0], nullptr);
    EXPECT_EQ(drivers[1], nullptr);
    EXPECT_EQ(drivers[2], nullptr);
    EXPECT_EQ(drivers[3], nullptr);

    EXPECT_STREQ(drivers[0]->driver->expression, "0.5");
  }

  /* Suzanne quaternion: get second element driver. Since there is none, we
   * should get back an empty vector, indicating that no drivers were found. */
  {
    bool is_array_prop;
    Vector<FCurve *> drivers = internal::get_property_drivers(
        &suzanne_ptr, suzanne_quaternion_prop, false, 1, &is_array_prop);

    EXPECT_EQ(drivers.size(), 0);
  }

  /* Suzanne rotation mode: get driver. */
  {
    bool is_array_prop;
    Vector<FCurve *> drivers = internal::get_property_drivers(
        &suzanne_ptr, suzanne_rotation_mode_prop, false, 0, &is_array_prop);

    EXPECT_EQ(is_array_prop, false);
    EXPECT_EQ(drivers.size(), 1);
    EXPECT_STREQ(drivers[0]->driver->expression, "4");
  }
}

TEST_F(CopyDriversToSelected, paste_property_drivers)
{
  /* Copy all quaternion channel drivers from Suzanne to Cube. The result on
   * Cube should be the following:
   *
   * - [0]: overwritten by the driver from Suzanne.
   * - [1]: Cube's driver remains, since there was no driver here on Suzanne.
   * - [2]: Suzanne's driver is pasted.  There was no driver on Cube before.
   * - [3]: remains without a driver.  Cube has animation on this channel,
   *   preventing driver pasting.
   */
  {
    bool is_array_prop;
    Vector<FCurve *> suzanne_location_drivers = internal::get_property_drivers(
        &suzanne_ptr, suzanne_quaternion_prop, true, -1, &is_array_prop);

    internal::paste_property_drivers(
        suzanne_location_drivers.as_span(), is_array_prop, &cube_ptr, cube_quaternion_prop);

    Vector<FCurve *> cube_location_drivers = internal::get_property_drivers(
        &cube_ptr, cube_quaternion_prop, true, -1, &is_array_prop);

    EXPECT_NE(cube_location_drivers[0], nullptr);
    EXPECT_NE(cube_location_drivers[1], nullptr);
    EXPECT_NE(cube_location_drivers[2], nullptr);
    EXPECT_EQ(cube_location_drivers[3], nullptr);

    EXPECT_STREQ(cube_location_drivers[0]->driver->expression, "0.5");
    EXPECT_STREQ(cube_location_drivers[1]->driver->expression, "1.0");
    EXPECT_STREQ(cube_location_drivers[2]->driver->expression, "2.5");
  }

  /* Copy the rotation_mode driver from Suzanne to Cube. */
  {
    bool is_array_prop;
    Vector<FCurve *> suzanne_rotation_mode_driver = internal::get_property_drivers(
        &suzanne_ptr, suzanne_rotation_mode_prop, false, 0, &is_array_prop);

    internal::paste_property_drivers(
        suzanne_rotation_mode_driver.as_span(), is_array_prop, &cube_ptr, cube_rotation_mode_prop);

    Vector<FCurve *> cube_rotation_mode_drivers = internal::get_property_drivers(
        &cube_ptr, cube_rotation_mode_prop, false, 0, &is_array_prop);

    EXPECT_NE(cube_rotation_mode_drivers[0], nullptr);
    EXPECT_STREQ(cube_rotation_mode_drivers[0]->driver->expression, "4");
  }
}

}  // namespace blender::ui::tests
