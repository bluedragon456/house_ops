# AGENTS.md

## Project
HouseOps

## Purpose
HouseOps is a Home Assistant custom integration for tracking recurring household equipment maintenance. Agents should treat this repository as the source of truth and build context from the code and docs before making changes.

## Workspace Notes
The active local workspace for this repository is:

`C:\dev\house_ops`

This project was previously worked on from a OneDrive-based path. Any older thread or workspace references that point to the old location should be treated as historical only and should not override the current local path.

## Agent Instructions
When assisting in this repository:

1. Read this file first.
2. Treat `C:\dev\house_ops` as the active project root.
3. Inspect the repository structure before making assumptions.
4. Prefer current repo files over chat memory when they conflict.
5. Preserve in-progress user work unless explicitly asked to change it.
6. Make focused changes that fit the existing Home Assistant integration patterns.
7. Explain changes clearly and keep recommendations practical.

## Product Context
HouseOps currently provides:

1. A Home Assistant custom integration under `custom_components/house_ops`
2. A single-entry integration model that manages many equipment assets inside one config entry
3. Equipment flows for review, add, edit, and remove operations through `Configure`
4. Recurring maintenance tracking for furnace / HVAC, water heater, fire alarms / smoke detectors, and custom systems
5. Asset-level and task-level entities for dashboards and automations
6. A Lovelace dashboard strategy in `www/house_ops/house-ops-strategy.js`

## Main Entry Points
Agents should inspect these files early when relevant:

1. `README.md`
2. `AGENTS.md`
3. `custom_components/house_ops/manifest.json`
4. `custom_components/house_ops/__init__.py`
5. `custom_components/house_ops/config_flow.py`
6. `custom_components/house_ops/coordinator.py`
7. `custom_components/house_ops/maintenance_engine.py`
8. `custom_components/house_ops/engine.py`
9. `custom_components/house_ops/registry.py`
10. `custom_components/house_ops/models.py`
11. `custom_components/house_ops/services.py`
12. `www/house_ops/house-ops-strategy.js`

## Repo Conventions
Follow these principles unless the repo clearly indicates otherwise:

1. Prefer minimal, targeted changes over rewrites.
2. Preserve the current integration structure and naming.
3. Keep Home Assistant flow behavior and stored data compatibility in mind.
4. Avoid unnecessary dependencies or file churn.
5. Add comments only when they clarify non-obvious logic.
6. Flag assumptions, risks, and migration implications clearly.

## Durable Context
Important durable context for future sessions:

1. The integration domain is `house_ops`.
2. The repo is intended to be usable as a public repository, so durable context should stay appropriate for public source control.
3. The codebase already uses config flows and options flows as the main equipment-management UX.
4. The options flow is the primary place for reviewing, adding, editing, and removing systems after setup.
5. Existing stored data should be treated carefully to avoid breaking users upgrading the integration.
6. Repo documentation should carry important long-term context instead of relying on old threads.

## Expected Workflow
For most tasks:

1. Read `AGENTS.md` and `README.md`.
2. Inspect the affected files and nearby patterns.
3. Summarize the current state briefly before major changes.
4. Make focused edits.
5. Verify changes where practical.
6. Report what changed, what was verified, and any follow-up items.

## When Starting A New Session
A new agent or session should:

1. Read `AGENTS.md`.
2. Confirm the active workspace is `C:\dev\house_ops`.
3. Inspect the repo structure.
4. Identify the stack and main entry points.
5. Summarize the current state of the integration before making major changes.
6. Continue using repo context as the main project memory source.

## Notes
If additional long-term guidance becomes important, add it here only if it belongs in a public repo.
