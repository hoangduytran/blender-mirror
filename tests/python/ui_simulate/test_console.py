# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Interaction tests for Python Console text selection."""

import modules.ui_test_utils as ui


def _setup_console(window):
    """Change the largest area to a Console and return its window region."""
    area = ui.largest_area(window.screen)
    area.type = 'CONSOLE'
    region = next(region for region in area.regions if region.type == 'WINDOW')
    return area, area.spaces.active, region


def _append_output(area, region, line_count=120):
    """Add enough source-shaped output to make the Console scrollable."""
    import bpy

    with bpy.context.temp_override(area=area, region=region):
        for index in range(line_count):
            bpy.ops.console.scrollback_append(
                text=(
                    f"source-row-{index:03d}: "
                    "    self.report({'ERROR'}, 'continued selection test output')"
                ),
                type='OUTPUT',
            )


def _point(region, x_factor, y_factor):
    """Return a window-space point inside a region."""
    return (
        region.x + round(region.width * x_factor),
        region.y + round(region.height * y_factor),
    )


def selection_shift_click_continues_existing_range():
    """Shift-click must continue a selection after the Console view moves."""
    e, t, window = ui.test_window()
    area, space, region = _setup_console(window)
    yield

    _append_output(area, region)
    yield

    first_start = _point(region, 0.25, 0.25)
    first_end = _point(region, 0.70, 0.45)

    e.cursor_position_set(*first_start, move=True)
    yield
    yield e.leftmouse.press()
    e.cursor_position_set(*first_end, move=True)
    yield
    yield e.leftmouse.release()
    yield

    initial_range = (space.select_start, space.select_end)
    t.assertLess(initial_range[0], initial_range[1])

    e.cursor_position_set(*_point(region, 0.5, 0.5), move=True)
    yield e.wheelup(8)
    yield

    e.cursor_position_set(*_point(region, 0.20, 0.80), move=True)
    yield
    yield e.shift.leftmouse()
    yield

    continued_range = (space.select_start, space.select_end)
    old_endpoint_preserved = (
        continued_range[0] == initial_range[0] or
        continued_range[1] == initial_range[1]
    )

    t.assertNotEqual(
        continued_range,
        initial_range,
        "Shift-click should move one endpoint of the selection",
    )
    t.assertTrue(
        old_endpoint_preserved,
        "Shift-click should preserve one old endpoint as the anchor",
    )
    t.assertLess(continued_range[0], continued_range[1])
