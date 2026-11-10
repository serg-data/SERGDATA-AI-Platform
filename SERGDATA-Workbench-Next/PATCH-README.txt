SERGDATA Workbench — additive Knowledge/picker/language patch
Build date: 2026-11-07

Included files (replace only these files):
- main.py
- static/app.js
- static/index.html

Changes:
- Adds a local native Windows file/folder picker endpoint (/api/local-dialog).
- Replaces the new-project path prompt with a project dialog and Browse button.
- Adds folder/file browse buttons to the existing AI-Knowledge selective indexing dialog.
- Adds missing English translations for visible More-menu / Knowledge labels and updates JS cache version.
- Does not modify Workbench DB, Git state, .env, .workbench, SSH material, or AI-Knowledge data/index.

Before installation:
1. Stop Workbench.
2. Back up the three target files.
3. Extract this ZIP into the Workbench root, preserving folder structure.
4. Start Workbench and verify project folder selection and Knowledge dialog.

Rollback:
Restore the three backed-up files and restart Workbench.

Validation performed in build environment:
- python -m py_compile main.py — passed
- node --check static/app.js — passed
Not performed: live Windows tkinter dialog test, browser interaction test, full Workbench regression suite.

SHA256:
7cff1aae0ccd9525b01ae7872975aa22326d7622093a541c8e8eabeec3c15498  main.py
07cd161b3c655bc89fb161c57e3fb5b5bb7a3c1049d78ad99c99a971735ef215  static/app.js
67e66b37423b7bb12578faf60e2a180fe17c5bb6c4f9de7c5662a571538732cf  static/index.html
