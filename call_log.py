import csv
import holidays
from datetime import date, datetime, timedelta
from pathlib import Path

FILE_NAME = Path("call_log.csv")
CONTACT_FILE = Path("contacts.csv")

# TODO(job_sites.csv): Project names must be unique across the whole company, not
# just per city — two subdivisions in different towns must not share a name, or the
# City lookup will return the wrong result. Not enforced yet since job_sites.csv
# doesn't exist; revisit when that file and its City/Area lookup are built.
HEADERS = ["ID", "Time", "Name", "Company", "Phone", "Email", "Address", "Project", "Reason", "Status", "Scheduled", "Assigned To", "Last Contacted", "Call Type", "Emergency", "Locate Requested", "Locate Clear Date", "Earliest Dig Date", "Job Category", "Estimated Duration", "Estimated End Date"]
CONTACT_HEADERS = ["Name", "Company", "Phone", "Email", "Address", "Notes"]

PROJECT_COL = 7
STATUS_COL = 9
SCHEDULED_COL = 10
ASSIGNED_TO_COL = 11
LAST_CONTACTED_COL = 12
CALL_TYPE_COL = 13
EMERGENCY_COL = 14
LOCATE_REQUESTED_COL = 15
LOCATE_CLEAR_COL = 16
EARLIEST_DIG_COL = 17
JOB_CATEGORY_COL = 18
ESTIMATED_DURATION_COL = 19
ESTIMATED_END_DATE_COL = 20

STATUSES = {
    "1": "Open",
    "2": "In Progress",
    "3": "Completed",
    "4": "Lost",
}

ACTIVE_STATUSES = {"Open", "In Progress"}

CALL_TYPES = {
    "1": "Sewer and Water Install",
    "2": "Sewer Install",
    "3": "Water Install",
    "4": "Septic Install",
    "5": "Misc. Install",
    "6": "Bid Work",
    "7": "Meter Pit Repair",
    "8": "Small Repair",
    "9": "Emergency Repair",
    "10": "Irrigation Install",
    "11": "Irrigation Repair",
}

# Call types that always require an 811 locate — the 3-business-day calculation
# runs automatically, no need to ask.
AUTO_LOCATE_CALL_TYPES = {
    "Sewer and Water Install", "Sewer Install", "Water Install",
    "Septic Install", "Misc. Install", "Irrigation Install",
}

# Call types where a locate is sometimes needed — ask each time.
ASK_LOCATE_CALL_TYPES = {
    "Meter Pit Repair", "Small Repair", "Emergency Repair", "Irrigation Repair",
}

# Anything not in either set above (e.g. Bid Work) gets no locate logic at all —
# no digging happens at that stage.

JOB_CATEGORIES = {
    "1": "Contract",
    "2": "Custom",
}


def pause():
    input("\nPress Enter to return to menu...")


def read_rows(file_path: Path) -> list[list[str]]:
    if not file_path.exists():
        return []
    with file_path.open(newline="") as file:
        return list(csv.reader(file))


def write_rows(rows: list[list[str]]) -> None:
    with FILE_NAME.open("w", newline="") as file:
        csv.writer(file).writerows(rows)


# --- helpers ---

def normalize_phone(phone: str) -> str:
    return phone.replace("-", "").replace(" ", "")


def prompt_phone(prompt_text: str) -> str:
    while True:
        phone = input(prompt_text)
        digits = normalize_phone(phone)
        if digits.isdigit() and len(digits) == 10:
            return phone
        print("Phone number must be 10 digits.")


def pad_row(row: list[str]) -> list[str]:
    padded = row + [""] * (len(HEADERS) - len(row))
    return padded[:len(HEADERS)]


def get_call_rows() -> list[list[str]]:
    rows = read_rows(FILE_NAME)
    return [pad_row(row) for row in rows[1:]] if rows else []


def ensure_call_file_schema() -> None:
    rows = read_rows(FILE_NAME)
    if not rows:
        return

    needs_update = rows[0] != HEADERS
    padded_rows = [HEADERS]

    for row in rows[1:]:
        padded = pad_row(row)
        if padded != row or needs_update:
            needs_update = True
        padded_rows.append(padded)

    if needs_update:
        write_rows(padded_rows)


def parse_call_date(row: list[str]):
    try:
        return datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S").date()
    except (ValueError, IndexError):
        return None


def parse_scheduled(value: str):
    if not value or not value.strip():
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def format_scheduled(value: str) -> str:
    parsed = parse_scheduled(value)
    if parsed:
        return parsed.strftime("%Y-%m-%d")
    return value or "Not scheduled"


def add_business_days(start_date: date, num_days: int) -> date:
    # Advances start_date by num_days business days, skipping weekends and US
    # federal holidays. This is a legal compliance calculation — Colorado 811
    # requires utilities to respond within 3 business days of a locate request.
    # Do not replace with a simple timedelta without verifying 811 rules still hold.
    us_holidays = holidays.US()
    current = start_date
    days_added = 0
    while days_added < num_days:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in us_holidays:
            days_added += 1
    return current


def calculate_locate_dates(emergency: str, base_date: date) -> tuple[str, str, str]:
    # Returns (locate_requested, locate_clear_date, earliest_dig_date) as
    # YYYY-MM-DD strings, or ("", "", "") when locate doesn't apply.
    # Whether to call this at all is decided by the caller based on Call Type
    # (see AUTO_LOCATE_CALL_TYPES / ASK_LOCATE_CALL_TYPES in log_call()) — this
    # function only knows how to do the date math, not which calls need it.
    # Locate Clear Date = 3 business days from Locate Requested.
    # Earliest Dig Date = calendar day after Locate Clear Date (not business day —
    # the crew can start digging the morning after utilities are marked, even on Monday
    # after a Friday clear date).
    # The Emergency flag (separate from the "Emergency Repair" Call Type) bypasses
    # locate timing entirely, regardless of Call Type, since digging can start immediately.
    if emergency.upper() == "Y":
        return "", "", ""
    locate_clear = add_business_days(base_date, 3)
    earliest_dig = locate_clear + timedelta(days=1)
    return (
        base_date.strftime("%Y-%m-%d"),
        locate_clear.strftime("%Y-%m-%d"),
        earliest_dig.strftime("%Y-%m-%d"),
    )


def prompt_call_type() -> str:
    print("\nCall Type:")
    for key, label in CALL_TYPES.items():
        print(f"{key}. {label}")
    choice = input("Select call type (1-11): ").strip()
    return CALL_TYPES.get(choice, "")


def prompt_job_category() -> str:
    # Job Category only applies to the auto-locate install types.
    # Contract = 2 addresses per crew, same project, completed same-day (dig,
    # install, inspect, backfill) — tracked via a shared Project so both
    # addresses share one Scheduled date.
    # Custom = a single install spanning 1-3+ days, tracked via Estimated
    # Duration (business days) with an auto-calculated Estimated End Date.
    print("\nJob Category:")
    for key, label in JOB_CATEGORIES.items():
        print(f"{key}. {label}")
    choice = input("Select job category (1-2): ").strip()
    return JOB_CATEGORIES.get(choice, "")


def format_call_line(row: list[str]) -> str:
    row = pad_row(row)
    scheduled = format_scheduled(row[SCHEDULED_COL])
    return (
        f"ID: {row[0]} | "
        f"Time: {row[1]} | "
        f"Name: {row[2]} | "
        f"Company: {row[3]} | "
        f"Phone: {row[4]} | "
        f"Reason: {row[8]} | "
        f"Status: {row[STATUS_COL]} | "
        f"Scheduled: {scheduled}"
    )


def format_call_detail(row: list[str]) -> str:
    row = pad_row(row)
    lines = []

    for i, header in enumerate(HEADERS):
        value = row[i]
        label = "Date" if header == "Time" else header

        if header == "Scheduled":
            # Always shown — format_scheduled() returns a "Not scheduled" placeholder
            # for a blank value rather than an empty string, so this isn't skipped.
            lines.append(f"{label}: {format_scheduled(value)}")
            continue

        if not value:
            continue

        if header == "Estimated Duration":
            value = f"{value} day(s)"

        lines.append(f"{label}: {value}")

    return "\n".join(lines)


def prompt_scheduled() -> str:
    date_str = input("Scheduled date (YYYY-MM-DD or MM/DD/YYYY, blank to clear): ").strip()
    if not date_str:
        return ""

    parsed = parse_scheduled(date_str)
    if not parsed:
        print("Invalid date format.")
        return prompt_scheduled()

    return parsed.strftime("%Y-%m-%d")


def is_active(row: list[str]) -> bool:
    return pad_row(row)[STATUS_COL] in ACTIVE_STATUSES


def get_due_date(row: list[str]):
    row = pad_row(row)
    scheduled = parse_scheduled(row[SCHEDULED_COL])
    if scheduled:
        return scheduled.date()
    return parse_call_date(row)


def is_overdue(row: list[str]) -> bool:
    if not is_active(row):
        return False
    due_date = get_due_date(row)
    return due_date is not None and due_date < datetime.now().date()


def is_this_week(row: list[str]) -> bool:
    if not is_active(row):
        return False

    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    due_date = get_due_date(row)
    return due_date is not None and week_start <= due_date <= week_end


def days_overdue(row: list[str]) -> int:
    due_date = get_due_date(row)
    if not due_date:
        return 0
    return (datetime.now().date() - due_date).days


def search_in_rows(rows: list[list[str]], query: str) -> list[list[str]]:
    return [
        row
        for row in rows
        if row and len(row) >= 2 and query in " ".join(row).lower()
    ]


def search_rows(query: str) -> list[list[str]]:
    return search_in_rows(get_call_rows(), query)


def show_calls(title: str, calls: list[list[str]], empty_message: str, detailed: bool = False) -> None:
    print(f"\n--- {title} ---\n")

    if not read_rows(FILE_NAME):
        print("No calls logged yet.")
        pause()
        return

    if not calls:
        print(empty_message)
    elif detailed:
        print("\n\n".join(format_call_detail(row) + "\n" + "-" * 40 for row in calls))
    else:
        for row in calls:
            print(format_call_line(row))

    pause()


def prompt_status() -> str:
    print("\nStatus options:")
    for key, label in STATUSES.items():
        print(f"{key}. {label}")
    status_choice = input("Select status (1-4): ")
    return STATUSES.get(status_choice, "Open")


def generate_id() -> int:
    ids = []
    for row in get_call_rows():
        try:
            ids.append(int(row[0]))
        except (ValueError, IndexError):
            pass
    return max(ids) + 1 if ids else 1


def select_call(query: str) -> tuple[list[list[str]], list[str]] | tuple[None, None]:
    matches = search_rows(query)

    if not matches:
        print("\nNo matching calls found.")
        return None, None

    print("\nMatching Calls:\n")
    for i, row in enumerate(matches, start=1):
        print(f"{i}. ID:{row[0]} | {row[2]} | {row[3]} | {pad_row(row)[STATUS_COL]}")

    choice = input("\nSelect a call: ")
    if not choice.isdigit() or not 1 <= int(choice) <= len(matches):
        print("\nInvalid selection.")
        return None, None

    selected = matches[int(choice) - 1]
    rows = read_rows(FILE_NAME)

    for i, row in enumerate(rows):
        if row and row[0] == selected[0]:
            rows[i] = pad_row(row)
            return rows, rows[i]

    print("\n⚠️ Call not found.")
    return None, None


def find_contact_index(phone: str):
    for i, row in enumerate(read_contacts()):
        if row and len(row) >= 3 and normalize_phone(row[2]) == normalize_phone(phone):
            return i
    return None


def add_contact(name: str, company: str, phone: str, email: str = "", address: str = "") -> None:
    clean_phone = normalize_phone(phone)
    for row in read_contacts():
        if row and len(row) >= 3 and normalize_phone(row[2]) == clean_phone:
            return

    file_exists = CONTACT_FILE.exists()
    with CONTACT_FILE.open("a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(CONTACT_HEADERS)
        writer.writerow([name, company, phone, email, address, ""])


def update_contact(name: str, company: str, phone: str, email: str = "", address: str = "") -> None:
    contacts = read_contacts()
    index = find_contact_index(phone)

    if index is not None:
        existing = contacts[index]
        notes = existing[5] if len(existing) > 5 else ""
        contacts[index] = [name, company, phone, email, address, notes]
    else:
        contacts.append([name, company, phone, email, address, ""])

    if contacts and contacts[0] != CONTACT_HEADERS:
        contacts.insert(0, CONTACT_HEADERS)
    elif not contacts:
        contacts = [CONTACT_HEADERS]

    write_contacts(contacts)


def read_contacts() -> list[list[str]]:
    return read_rows(CONTACT_FILE)


def write_contacts(rows: list[list[str]]) -> None:
    with CONTACT_FILE.open("w", newline="") as file:
        csv.writer(file).writerows(rows)


def find_or_create_contact(phone: str) -> dict | None:
    contacts = read_contacts()
    index = find_contact_index(phone)
    if index is None:
        return None
    saved = contacts[index]
    return {
        "name":    saved[0] if len(saved) > 0 else "",
        "company": saved[1] if len(saved) > 1 else "",
        "email":   saved[3] if len(saved) > 3 else "",
    }


def find_prior_project(phone: str) -> list[str] | None:
    prior_calls = [
        r for r in get_call_rows()
        if normalize_phone(r[4]) == normalize_phone(phone) and pad_row(r)[PROJECT_COL]
    ]
    return pad_row(prior_calls[-1]) if prior_calls else None


def create_call_record(
    phone: str,
    name: str,
    company: str,
    email: str,
    address: str,
    project: str,
    reason: str,
    status: str,
    scheduled: str,
    call_type: str = "",
    emergency: str = "",
    locate_requested: str = "",
    locate_clear: str = "",
    earliest_dig: str = "",
    job_category: str = "",
    estimated_duration: str = "",
    estimated_end_date: str = "",
) -> list[str]:
    row = [
        str(generate_id()),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        name,
        company,
        phone,
        email,
        address,
        project,
        reason,
        status,
        scheduled,
        "",              # Assigned To
        "",              # Last Contacted
        call_type,
        emergency,
        locate_requested,
        locate_clear,
        earliest_dig,
        job_category,
        estimated_duration,
        estimated_end_date,
    ]

    file_exists = FILE_NAME.exists()
    with FILE_NAME.open("a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(HEADERS)
        writer.writerow(row)

    add_contact(name, company, phone, email, address)
    return row


def log_call():
    print("\n--- Construction Call Tracker ---\n")

    phone = prompt_phone("Phone Number: ")

    saved_contact = find_or_create_contact(phone)

    if saved_contact is not None:
        print(f"\nFound contact:")
        print(f"  Name:    {saved_contact['name']}")
        print(f"  Company: {saved_contact['company']}")
        print(f"  Email:   {saved_contact['email']}")

        use = input("\nUse this info? (y/n): ").lower().strip()

        if use == "y":
            name    = saved_contact["name"]
            company = saved_contact["company"]
            email   = saved_contact["email"]
        else:
            print("\nWhat changed? (press Enter to keep saved value)")
            val = input(f"Name [{saved_contact['name']}]: ").strip()
            name = val if val else saved_contact["name"]

            val = input(f"Company [{saved_contact['company']}]: ").strip()
            company = val if val else saved_contact["company"]

            val = input(f"Email [{saved_contact['email']}]: ").strip()
            email = val if val else saved_contact["email"]
    else:
        name    = input("Customer Name: ")
        company = input("Company: ")
        email   = input("Email: ")

    # Project auto-fill applies to every Call Type, not just installs. It also
    # tracks whether the Project matched an existing call — and that call's
    # Scheduled date — so Contract jobs can sync their schedule to it later.
    project = ""
    linked_scheduled = ""

    if saved_contact is not None:
        prior_call = find_prior_project(phone)
        if prior_call:
            prior_project = prior_call[PROJECT_COL]
            same = input(f"Same project — {prior_project}? (y/n): ").lower().strip()
            if same == "y":
                project = prior_project
                linked_scheduled = prior_call[SCHEDULED_COL]

    if not project:
        search = input("Search existing projects? (y/n): ").lower().strip()
        if search == "y":
            query = input("Search Project: ").lower().strip()
            matches = search_in_rows(
                [r for r in get_call_rows() if pad_row(r)[PROJECT_COL]], query
            )

            if matches:
                print("\nMatching Projects:\n")
                for i, r in enumerate(matches, start=1):
                    r = pad_row(r)
                    print(
                        f"{i}. ID:{r[0]} | {r[2]} | "
                        f"Project: {r[PROJECT_COL]} | "
                        f"Scheduled: {format_scheduled(r[SCHEDULED_COL])}"
                    )
                choice = input("\nSelect a project: ")
                if choice.isdigit() and 1 <= int(choice) <= len(matches):
                    linked = pad_row(matches[int(choice) - 1])
                    project = linked[PROJECT_COL]
                    linked_scheduled = linked[SCHEDULED_COL]
                else:
                    print("\nInvalid selection.")
            else:
                print("\nNo matching projects found.")

    if not project:
        project = input("Project: ")

    address = input("Address: ")
    reason = input("Reason for call: ")
    call_type = prompt_call_type()
    emergency = input("Emergency (Y/N): ").strip().upper()
    status = prompt_status()

    schedule = input("\nSchedule follow-up? (y/n): ").lower().strip()
    scheduled = prompt_scheduled() if schedule == "y" else ""

    today = datetime.now().date()
    if call_type in AUTO_LOCATE_CALL_TYPES:
        locate_requested, locate_clear, earliest_dig = calculate_locate_dates(emergency, today)
    elif call_type in ASK_LOCATE_CALL_TYPES:
        needs_locate = input("Does this repair need a locate? (y/n): ").lower().strip()
        if needs_locate == "y":
            locate_requested, locate_clear, earliest_dig = calculate_locate_dates(emergency, today)
        else:
            locate_requested, locate_clear, earliest_dig = "", "", ""
    else:
        # e.g. Bid Work — no digging happens at this stage, no locate logic at all
        locate_requested, locate_clear, earliest_dig = "", "", ""

    job_category = ""
    estimated_duration = ""
    estimated_end_date = ""

    if call_type in AUTO_LOCATE_CALL_TYPES:
        job_category = prompt_job_category()

        if job_category == "Contract" and linked_scheduled:
            # Contract: 2 addresses per crew, same project, completed same-day.
            # Both addresses share one Project and the same Scheduled date, so a
            # Contract call that matched an existing Project inherits that
            # Project's Scheduled date instead of using whatever was entered above.
            # This sync is Contract-only — Custom installs and repairs that reuse
            # a Project name never have their Scheduled date overwritten this way.
            scheduled = linked_scheduled

        elif job_category == "Custom":
            # Custom: a single install spanning 1-3+ days. Estimated Duration is
            # business days (weekends skipped); Estimated End Date is calculated
            # from the Scheduled start date using the same add_business_days()
            # math as locates — a duration of 1 means the job starts and ends
            # the same day, so 0 additional business days are added.
            duration_input = input("Estimated Duration (business days, blank for 1): ").strip()
            try:
                duration = int(duration_input) if duration_input else 1
            except ValueError:
                duration = 1
            estimated_duration = str(duration)

            start = parse_scheduled(scheduled)
            if start:
                estimated_end_date = add_business_days(start.date(), duration - 1).strftime("%Y-%m-%d")

    create_call_record(
        phone, name, company, email, address, project, reason, status, scheduled,
        call_type, emergency, locate_requested, locate_clear, earliest_dig,
        job_category, estimated_duration, estimated_end_date,
    )

    print("\n✅ Call logged successfully!")
    pause()


def view_calls():
    open_calls = [row for row in get_call_rows() if pad_row(row)[STATUS_COL] == "Open"]
    show_calls("OPEN CALLS", open_calls, "No open calls.", detailed=True)


def open_today():
    today = datetime.now().date()
    today_calls = [
        row
        for row in get_call_rows()
        if is_active(row) and get_due_date(row) == today
    ]
    show_calls("OPEN TODAY", today_calls, "No calls due today.", detailed=True)


def open_overdue():
    overdue_calls = sorted(
        [row for row in get_call_rows() if is_overdue(row)],
        key=lambda row: get_due_date(row) or datetime.min.date(),
    )

    print("\n--- OPEN OVERDUE ---\n")

    if not read_rows(FILE_NAME):
        print("No calls logged yet.")
        pause()
        return

    if not overdue_calls:
        print("No overdue open calls.")
    else:
        for row in overdue_calls:
            overdue_days = days_overdue(row)
            print(format_call_line(row))
            print(f"Overdue by {overdue_days} day{'s' if overdue_days != 1 else ''}")
            print("-" * 40)

    pause()


def open_this_week():
    week_calls = sorted(
        [row for row in get_call_rows() if is_this_week(row)],
        key=lambda row: get_due_date(row) or datetime.max.date(),
    )
    show_calls("OPEN THIS WEEK", week_calls, "No open calls due this week.")


def open_queue():
    active_calls = [row for row in get_call_rows() if is_active(row)]
    show_calls("OPEN CALL QUEUE", active_calls, "🎉 No active calls. Everything is cleared.")


def search_call():
    print("\n--- SEARCH CALLS ---\n")
    query = input("Search by name, phone, company, or reason: ").lower().strip()

    rows = get_call_rows()
    if not rows:
        print("No calls logged yet.")
        pause()
        return

    matches = search_in_rows(rows, query)
    if matches:
        for row in matches:
            print(format_call_line(row))
    else:
        print("No matching calls found.")

    pause()


def edit_call():
    print("\n--- EDIT CALL ---\n")
    query = input("Search call (name, phone, company, reason): ").lower().strip()

    rows, row = select_call(query)
    if row is None:
        pause()
        return

    print("\nSelected Call:")
    print(format_call_detail(row))

    print("\nWhat would you like to do?")
    print("1. Name")
    print("2. Company")
    print("3. Phone")
    print("4. Email")
    print("5. Address")
    print("6. Project")
    print("7. Reason")
    print("8. Status")
    print("9. Mark as Completed")
    print("10. Set Schedule")
    print("11. Assigned To")
    print("12. Cancel")

    action = input("\nSelect option: ")

    if action == "1":
        row[2] = input("Enter new name: ")
    elif action == "2":
        row[3] = input("Enter new company: ")
    elif action == "3":
        row[4] = prompt_phone("Enter new phone: ")
    elif action == "4":
        row[5] = input("Enter new email: ")
    elif action == "5":
        row[6] = input("Enter new address: ")
    elif action == "6":
        row[PROJECT_COL] = input("Enter new project: ")
    elif action == "7":
        row[8] = input("Enter new reason: ")
    elif action == "8":
        row = pad_row(row)
        row[STATUS_COL] = prompt_status()
    elif action == "9":
        row = pad_row(row)
        row[STATUS_COL] = "Completed"
        write_rows(rows)
        print("\n✅ Call marked as Completed!")
        pause()
        return
    elif action == "10":
        row = pad_row(row)
        row[SCHEDULED_COL] = prompt_scheduled()
        write_rows(rows)
        print("\n✅ Schedule updated!")
        pause()
        return
    elif action == "11":
        row = pad_row(row)
        row[11] = input("Assign to: ")
    elif action == "12":
        pause()
        return
    else:
        print("\nInvalid option.")
        pause()
        return

    write_rows(rows)
    print("\n✅ Call updated!")

    sync = input("\nUpdate contact phonebook too? (y/n): ").lower().strip()
    if sync == "y":
        update_contact(row[2], row[3], row[4], row[5], row[6])
        print("✅ Contact updated!")

    pause()


def mark_complete():
    print("\n--- MARK CALL AS COMPLETED ---\n")
    query = input("Search call (name, phone, company, reason): ").lower().strip()

    rows, row = select_call(query)
    if row is None:
        pause()
        return

    row = pad_row(row)
    if row[STATUS_COL] == "Completed":
        print("\nThis call is already marked as Completed.")
        pause()
        return

    confirm = input(f"\nMark call ID {row[0]} ({row[2]}) as Completed? (y/n): ").lower().strip()
    if confirm != "y":
        pause()
        return

    row = pad_row(row)
    row[STATUS_COL] = "Completed"
    write_rows(rows)
    print("\n✅ Call marked as Completed!")
    pause()


def schedule_call():
    print("\n--- SCHEDULE CALL ---\n")
    query = input("Search call (name, phone, company, reason): ").lower().strip()

    rows, row = select_call(query)
    if row is None:
        pause()
        return

    print("\nSelected Call:")
    print(format_call_detail(row))

    row = pad_row(row)
    row[SCHEDULED_COL] = prompt_scheduled()
    write_rows(rows)

    if row[SCHEDULED_COL]:
        print(f"\n✅ Call scheduled for {format_scheduled(row[SCHEDULED_COL])}!")
    else:
        print("\n✅ Schedule cleared.")

    pause()


def view_scheduled():
    scheduled_calls = sorted(
        [
            row for row in get_call_rows()
            if parse_scheduled(pad_row(row)[SCHEDULED_COL])
        ],
        key=lambda row: parse_scheduled(pad_row(row)[SCHEDULED_COL]),
    )
    show_calls("SCHEDULED CALLS", scheduled_calls, "No scheduled calls.")


def scheduled_today():
    today = datetime.now().date()
    today_scheduled = [
        row
        for row in get_call_rows()
        if (scheduled := parse_scheduled(pad_row(row)[SCHEDULED_COL]))
        and scheduled.date() == today
    ]
    show_calls("SCHEDULED TODAY", today_scheduled, "Nothing scheduled for today.", detailed=True)


def scheduled_this_week():
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    week_scheduled = sorted(
        [
            row for row in get_call_rows()
            if (scheduled := parse_scheduled(pad_row(row)[SCHEDULED_COL]))
            and week_start <= scheduled.date() <= week_end
        ],
        key=lambda row: parse_scheduled(pad_row(row)[SCHEDULED_COL]),
    )
    show_calls("SCHEDULED THIS WEEK", week_scheduled, "Nothing scheduled this week.")


def scheduling():
    views = {
        "1": schedule_call,
        "2": view_scheduled,
        "3": scheduled_today,
        "4": scheduled_this_week,
    }

    while True:
        print("\n--- SCHEDULING ---\n")
        print("1. Schedule a Call")
        print("2. View Scheduled Calls")
        print("3. Scheduled Today")
        print("4. Scheduled This Week")
        print("5. Back")

        choice = input("\nSelect option: ")

        if choice == "5":
            break

        view = views.get(choice)
        if view:
            view()
        else:
            print("Invalid choice.")


def view_contacts():
    print("\n--- CONTACT LIST ---\n")

    contacts = read_contacts()[1:]
    if not contacts:
        print("No contacts found.")
        pause()
        return

    for row in contacts:
        if len(row) < 3:
            continue
        email = row[3] if len(row) > 3 else ""
        print(f"Name: {row[0]} | Company: {row[1]} | Phone: {row[2]} | Email: {email}")

    pause()


def search_contacts():
    print("\n--- SEARCH CONTACTS ---\n")
    query = input("Search by name, company, or phone: ").lower().strip()

    contacts = read_contacts()[1:]
    if not contacts:
        print("No contacts found.")
        pause()
        return

    matches = search_in_rows(contacts, query)
    if matches:
        for row in matches:
            email = row[3] if len(row) > 3 else ""
            print(f"Name: {row[0]} | Company: {row[1]} | Phone: {row[2]} | Email: {email}")
    else:
        print("No matching contacts found.")

    pause()


def edit_contact():
    print("\n--- EDIT CONTACT ---\n")
    query = input("Search name, company, or phone: ").lower().strip()

    contacts = read_contacts()
    if len(contacts) <= 1:
        print("No contacts found.")
        pause()
        return

    matches = search_in_rows(contacts[1:], query)
    if not matches:
        print("No matching contacts found.")
        pause()
        return

    print("\nMatching Contacts:\n")
    for i, row in enumerate(matches, start=1):
        print(f"{i}. {row[0]} | {row[1]} | {row[2]}")

    choice = input("\nSelect contact: ")
    if not choice.isdigit():
        print("Invalid selection.")
        pause()
        return

    idx = int(choice) - 1
    if idx < 0 or idx >= len(matches):
        print("Invalid selection.")
        pause()
        return

    selected = matches[idx]

    print("\nWhat would you like to edit?")
    print("1. Name")
    print("2. Company")
    print("3. Phone")
    print("4. Email")
    print("5. Address")
    print("6. Notes")
    print("7. Cancel")

    action = input("\nSelect option: ")

    if action == "1":
        selected[0] = input("New name: ")
    elif action == "2":
        selected[1] = input("New company: ")
    elif action == "3":
        selected[2] = prompt_phone("New phone: ")
    elif action == "4":
        while len(selected) < 4:
            selected.append("")
        selected[3] = input("New email: ")
    elif action == "5":
        while len(selected) < 5:
            selected.append("")
        selected[4] = input("New address: ")
    elif action == "6":
        while len(selected) < 6:
            selected.append("")
        selected[5] = input("New notes: ")
    elif action == "7":
        pause()
        return
    else:
        print("Invalid option.")
        pause()
        return

    write_contacts(contacts)
    print("\n✅ Contact updated!")
    pause()


def customer_history():
    print("\n--- CUSTOMER HISTORY ---\n")
    query = input("Search by name, company, or phone: ").lower().strip()

    rows = get_call_rows()
    if not rows:
        print("No calls logged yet.")
        pause()
        return

    matches = search_in_rows(rows, query)
    if not matches:
        print("No matching history found.")
        pause()
        return

    print("\n--- HISTORY ---\n")
    print("\n\n".join(format_call_detail(row) + "\n" + "-" * 40 for row in matches))
    pause()


def dashboard():
    views = {
        "1": view_calls,
        "2": open_today,
        "3": open_overdue,
        "4": open_this_week,
        "5": scheduled_today,
        "6": scheduled_this_week,
    }

    while True:
        print("\n--- DASHBOARD ---\n")
        print("1. Open Calls")
        print("2. Open Today")
        print("3. Open Overdue")
        print("4. Open This Week")
        print("5. Scheduled Today")
        print("6. Scheduled This Week")
        print("7. Back")

        choice = input("\nSelect option: ")

        if choice == "7":
            break

        view = views.get(choice)
        if view:
            view()
        else:
            print("Invalid choice.")


def contact_manager():
    while True:
        print("\n--- CONTACT MANAGER ---\n")
        print("1. View Contacts")
        print("2. Search Contacts")
        print("3. Customer History")
        print("4. Edit Contact")
        print("5. Back")

        choice = input("\nSelect option: ")

        if choice == "1":
            view_contacts()
        elif choice == "2":
            search_contacts()
        elif choice == "3":
            customer_history()
        elif choice == "4":
            edit_contact()
        elif choice == "5":
            break
        else:
            print("Invalid choice.")


def main():
    ensure_call_file_schema()

    while True:
        print("\n--- Construction Call Menu ---\n")
        print("1. Log New Call")
        print("2. Open Queue")
        print("3. Search Calls")
        print("4. Edit Call")
        print("5. Mark Call Complete")
        print("6. Dashboard")
        print("7. Scheduling")
        print("8. Contact Manager")
        print("9. Exit")

        choice = input("\nSelect option: ")

        if choice == "1":
            log_call()
        elif choice == "2":
            open_queue()
        elif choice == "3":
            search_call()
        elif choice == "4":
            edit_call()
        elif choice == "5":
            mark_complete()
        elif choice == "6":
            dashboard()
        elif choice == "7":
            scheduling()
        elif choice == "8":
            contact_manager()
        elif choice == "9":
            break
        else:
            print("\nInvalid choice — try again.")


if __name__ == "__main__":
    main()
