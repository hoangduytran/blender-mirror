# Independent review of the smaller-design note

The recommendations pass review. They describe possible future changes, not changes already made or a replacement already proved. The working prototype remains intact.

ID.flag is the saved field and ID.tag is temporary. The note correctly requires checking past bit use and old-file conversion before choosing a flag. It does not pretend the suggested flag already exists. Removing the copied-name protection requires replacing the rename/final-name/copy rules, not simply deleting them.

A validated yes/no node-tool record can remove the extra property allocation while retaining the owned source name and refresh/hash rules. Unloaded assets still need saved permission information. Override decisions, factory authoring, source/translatable search and user rename behavior remain required. Editor work is proposed as a separate patch, not dropped behavior. The operator-wide name switch must remain until a complete safe alternative is proved. No measured speedup is claimed.

All local links resolve and the referenced functions and fields exist at the indicated source areas. One minor wording correction is needed: private descriptor helpers and constants are not public header declarations. Say the implementation is in id_ui_name.cc and the public BKE entry points are declared in BKE_id_ui_name.hh. No other content blocker found.
