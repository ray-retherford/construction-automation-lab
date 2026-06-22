# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Project

Construction office automation tool for a 7-person sewer/water lateral installation company
in Northern Colorado. Handles incoming calls, contact management, scheduling, and job tracking.
End goal: AI-assisted intake so routine calls, emails, and scheduling run without manual entry.

# Stack

- Language: Python 3.11+
- Data: CSV files (call_log.csv, contacts.csv)
- Interface: Terminal menu (expanding toward web dashboard and AI layer)
- No external dependencies yet — stdlib only

# Files

- call_log.py — main app, all logic lives here for now
- call_log.csv — persistent call records
- contacts.csv — customer/company phonebook synced from call logs

# Commands

- Run: `python3 call_log.py`
- No build, lint, or test step yet

# Rules

<!-- Code style -->
- Follow the existing pattern: small focused functions, descriptive names, no clever tricks
- Use type hints on all new functions (existing code uses them — keep it consistent)
- Keep CSV column order and HEADERS/CONTACT_HEADERS constants as the source of truth
- pad_row() must be called before accessing STATUS_COL or SCHEDULED_COL — always
- Date parsing goes through parse_scheduled() — do not add new date parsing logic elsewhere

<!-- Behavior -->
- Read the relevant functions before editing — many helpers are shared across features
- Make the smallest change that solves the problem
- Do not refactor existing working code unless explicitly asked
- If a change touches CSV structure, check pad_row() and ensure_call_file_schema() still work
- After finishing a task, list what changed and why in 2-3 lines

<!-- Output -->
- Be concise. Skip preamble. Show only changed sections, not whole file
- No print statements or debug code left in finished work

# Off Limits

- NEVER modify or delete call_log.csv or contacts.csv directly
- NEVER change the HEADERS or CONTACT_HEADERS constants without being asked
- NEVER change the STATUS_COL or SCHEDULED_COL index values without updating all references
- Do not add external libraries without asking first — stdlib preference for now

# Roadmap

<!-- Where this is going — helps Claude suggest next steps that fit the plan -->
Phase 1 (done): Terminal call logger with contacts, scheduling, and dashboard
Phase 2 (next): AI classification layer — read call/email input, suggest reason + status
Phase 3: Gmail integration — auto-log incoming emails as call records
Phase 4: Google Sheets sync — push job data to master schedule
Phase 5: Web dashboard — replace terminal menu with a simple browser UI

# Compaction

When compacting, preserve:
- Which files were changed this session
- Any decisions made about data structure or CSV schema
- The current task and next steps

# Notes

<!-- Update this as the project evolves -->
- All date logic uses parse_scheduled() — it handles 3 formats, do not bypass it
- normalize_phone() strips dashes and spaces — use it when comparing phone numbers
- select_call() returns (rows, row) or (None, None) — always check for None before using
