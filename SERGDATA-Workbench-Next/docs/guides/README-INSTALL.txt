SERGDATA Workbench — Vertical Resize Optimization

Based on archive: SERGDATA-Workbench-Next(20261107-115643).zip
Changed file: static/app.js only.

Purpose: constrain vertical resizing of the message history and PowerShell/SSH panel against the actual height of the pending area, resize grips, and composer. The composer is reserved first; the two resizable panels cannot consume its space.

No backend, database, credentials, project data, agent, approval, SSH, or LM Studio code is included or changed.

Install safely:
1. Stop Workbench.
2. Back up static/app.js.
3. Extract this archive into the Workbench root, replacing only static/app.js.
4. Restart Workbench and hard-refresh the browser (Ctrl+F5).

Rollback: restore the saved static/app.js.
