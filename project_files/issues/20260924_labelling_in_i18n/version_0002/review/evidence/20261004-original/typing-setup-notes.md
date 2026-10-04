# Native typing-test setup

The fresh root run without the established macOS window flags failed to locate the test button before typing. This is not a passing feature test.

An independent exact-window repeat passed the unchanged 14-variant event check. A synchronous redraw_timer experiment then crashed while locating a button; that experiment was removed and is not part of the delivered test. The final fixture only requests a normal header redraw and waits for the event loop before each activation/reopening. It keeps all typing, source-name and eligibility assertions.

No inaccessible screen or operating-system app-control workaround was used. The reviewer instructions retain the direct native child command and separate test resources. Final root repetition is recorded separately.
