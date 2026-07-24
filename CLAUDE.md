# Project

Construction office automation tool for a 7-person sewer/water lateral installation company
in Northern Colorado. Handles incoming calls, contact management, scheduling, dispatch, and
job tracking. End goal: AI-assisted intake so routine calls, emails, and scheduling run with
minimal manual entry.

# Stack

- Language: Python 3.11+
- Data: CSV files (call_log.csv, contacts.csv). Planned: employees.csv, job_sites.csv
- Interface: Terminal menu (expanding toward Google Sheets sync and AI layer)
- Dependencies: stdlib only, EXCEPT the `holidays` library — approved exception, used for
  accurate US federal holiday calculation in locate date math. This is a legal compliance
  calculation (811 locate law), so correctness matters more than dependency purity here.
  Do not add further external libraries without asking first.

# Files

- call_log.py — main app, all logic lives here for now
- call_log.csv — persistent call records
- contacts.csv — customer/company phonebook synced from call logs
- employees.csv (planned) — Name, Role (Operator/Labor), Default Partner
- job_sites.csv (planned) — Job Site, City/Area lookup

# Commands

- Run: `python3 call_log.py` (not `python` — this environment requires python3)
- No build, lint, or test step yet

# Business Rules (critical — do not guess, ask if unclear)

<!-- These reflect real operational and legal constraints. Get these wrong and it's not
     just a bug, it could mean a crew digging before locates are legally clear. -->

- **Assignment timing**: Operator/crew assignments are finalized around 3PM Mountain Time
  daily, after today's work is confirmed complete and tomorrow's inspections are called in.
  Dispatch is an end-of-day planning step, not a real-time assignment the moment a call
  comes in. Any automation must not attempt to auto-assign crews before this daily point.

- **Call Types and locate handling**:
  - **Auto-locate (3-business-day calculation always applies)**: Sewer and Water Install,
    Sewer Install, Water Install, Septic Install, Misc. Install, Irrigation Install
  - **Ask each time ("Does this need a locate? y/n")**: Meter Pit Repair, Small Repair,
    Emergency Repair, Irrigation Repair
  - **No locate logic at all**: Bid Work (no digging happens at bid stage)
  - Emergency flag (separate from Emergency Repair call type) bypasses locate timing
    entirely regardless of Call Type — used for true emergencies needing same-day digging

- **811 Locate law (auto-locate types)**: 3-business-day locate period before digging,
  skipping weekends AND US federal holidays. The locate ticket clears end-of-day on the 3rd
  business day; digging can legally start the following calendar day at 6 AM. So: Locate
  Clear Date = Locate Requested + 3 business days. Earliest Dig Date = Locate Clear Date +
  1 calendar day. The Emergency flag bypasses this entirely.

- **Repairs are handled opportunistically**, not scheduled like installs. They're logged
  throughout the day as they come in, added to an open list automatically, and assigned to a
  laborer only when one is confirmed nearby/in the area — to minimize drive time and gas.
  Most repairs are not urgent and can wait days until a crew is in the area. This should
  remain a human judgment call, not an automated assignment.

- **Call Type list** (final): Sewer and Water Install, Sewer Install, Water Install,
  Septic Install, Misc. Install, Bid Work, Meter Pit Repair, Small Repair, Emergency Repair,
  Irrigation Install, Irrigation Repair. See locate handling categorization above for which
  types trigger automatic vs ask-each-time vs no locate logic.

- **Contract vs Custom installs**: Contract work = 2 addresses per crew, same project,
  completed same-day (dig, install, inspect, backfill) — tracked via a shared Project Group
  so both addresses share a Scheduled date. Custom work = 1-3+ days, tracked via Estimated
  Duration (business days only, weekends skipped) with an auto-calculated Estimated End Date.

- **Crew structure**: Two-person teams (Operator + Labor), usually consistent pairs but not
  strict/fixed. After inspection passes on an install, the Operator stays to finish; the
  Labor hand splits off to work repairs at the same site or nearby. Do not model crews as
  rigid fixed pairs — use soft defaults (Default Partner) that can be overridden.

# Rules

<!-- Code style -->
- Follow the existing pattern: small focused functions, descriptive names, no clever tricks
- Use type hints on all new functions (existing code uses them — keep it consistent)
- Keep CSV column order and HEADERS/CONTACT_HEADERS constants as the source of truth
- pad_row() must be called before accessing any column by index — always
- Date parsing goes through parse_scheduled() — do not add new date parsing logic elsewhere
- Business-day math (locates, custom install duration) goes through one shared
  add_business_days() function — do not duplicate this logic
- Implement the simplest solution that works. Do not add flexibility that isn't needed yet.
- Do not touch code unrelated to the current task

<!-- Behavior — how Claude should work -->
- Ask before writing a single line if the request is unclear
- When running unattended, pick the most reasonable interpretation, proceed, and note the assumption
- If you discover bad code or design issues outside the current task, surface them as a separate note — do not fix them silently
- Flag uncertainty explicitly rather than proceeding with false confidence
- Read the relevant functions before editing — many helpers are shared across features
- Make the smallest change that solves the problem
- Do not refactor existing working code unless explicitly asked
- After finishing a task, summarize what changed and why in 2-3 lines

<!-- Three modes — be explicit about which one applies -->
- Mode 1 EXECUTE: carry out the request exactly as asked
- Mode 2 FLAG: if you see a clearly better approach, say so before implementing — explain the tradeoff in 2-4 bullets, then proceed unless the alternative avoids serious risk or wasted work
- Mode 3 STOP: refuse or pause if the requested path risks data loss, security issues, irreversible changes, or hours of wasted debugging

<!-- When to challenge vs just do it -->
- Challenge me when the alternative reduces: irreversible work, security risk, data loss, broad refactors, or hours of wasted debugging
- Do not challenge me just because there is a prettier abstraction or cleaner pattern
- If what we are building resembles settled industry practice or a known pattern, say so — reference how others solve it rather than reinventing from scratch

<!-- Output -->
- Be concise. Skip preamble. Show only changed sections, not the whole file
- No debug print statements left in finished work

# Off Limits

- NEVER modify or delete call_log.csv or contacts.csv directly
- NEVER change the HEADERS or CONTACT_HEADERS constants without being asked
- NEVER change column index constants without updating all references
- Do not add external libraries without asking first — the `holidays` library is the one
  approved exception (see Stack section)

# Roadmap

Phase 1 (done): Terminal call logger with contacts, scheduling, and dashboard
Phase 1.5 (done): Refactored log_call() into create_call_record() and
  find_or_create_contact() — pure logic, no input()/print(), so the same engine can be
  triggered by Terminal, a future voice agent, or automated Sheets sync
Phase 2 (in progress): Contact + Job Site auto-fill by phone, Call Type, Emergency flag,
  811 locate date calculations, Contract/Custom install scheduling with Project Group and
  Estimated Duration
Phase 2 (next): employees.csv and job_sites.csv, Dispatch view grouped by City/Area
Phase 3: Google Sheets sync — push Master Schedule (New Installs / Repairs) and pull
  Google Forms field employee reporting (Address, Parts Used, Labor Hours, Notes, Pictures)
Phase 4: Web dashboard — replace terminal menu with a simple browser UI
Phase 5: AI agent layer — answer phone, create call record, assign schedule, send texts,
  update Sheets
Future: Auto-fill locate dates from 811 website or email confirmation instead of manual entry

# Compaction

When compacting, preserve:
- Which files were changed this session
- Any decisions made about data structure, CSV schema, or business rules
- The current task and next steps

# Notes

- All date logic uses parse_scheduled() — it handles 3 formats, do not bypass it
- normalize_phone() strips dashes and spaces — use it when comparing phone numbers
- select_call() returns (rows, row) or (None, None) — always check for None before using
- Contact auto-fill only covers Name, Company, Email — Address was removed from this flow
  since it's not meaningful in this industry (customers are supervisors/warranty contacts,
  not billing relationships)
- Job Site auto-fill pulls from the most recent call record for that phone number, not from
  the contact record — Job Site and Address are separate concepts (project vs specific lot)
- Address is always asked fresh every call, never auto-filled, since it changes constantly
  even when Job Site stays the same
