import csv
from datetime import datetime
from pathlib import Path

FILE_NAME = Path("call_log.csv")
CONTACT_FILE = Path("contacts.csv")

HEADERS = ["ID", "Time", "Name", "Company", "Phone", "Reason", "Status"]
CONTACT_HEADERS = ["Name", "Company", "Phone"]

STATUSES = {
    "1": "Open",
    "2": "In Progress",
    "3": "Completed",
    "4": "Lost",
}


def pause():
    input("\nPress Enter to return to menu...")  


def normalize_phone(phone: str) -> str:
    return phone.replace("-", "").replace(" ", "")


def read_rows(file_path):
    if not file_path.exists():
        return []
    with file_path.open(newline="") as file:
        return list(csv.reader(file))

def write_rows(rows):
    with FILE_NAME.open("w", newline="") as file:
        csv.writer(file).writerows(rows)

def read_contacts():
    if not CONTACT_FILE.exists():
        return []

    with CONTACT_FILE.open(newline="") as file:
        return list(csv.reader(file))

def write_contacts(rows):
    with CONTACT_FILE.open("w", newline="") as file:
        csv.writer(file).writerows(rows)

def find_contact_index(phone):
    contacts = read_contacts()

    for i, row in enumerate(contacts):
        if row and len(row) >= 3:
            if normalize_phone(row[2]) == normalize_phone(phone):
                return i

    return None

def update_contact(name, company, phone):
    contacts = read_contacts()

    index = find_contact_index(phone)

    if index is not None:
        # update existing contact
        contacts[index][0] = name
        contacts[index][1] = company
        contacts[index][2] = phone
    else:
        # create new contact
        contacts.append([name, company, phone])

    write_contacts(contacts)

def log_call():
    print("\n--- Construction Call Tracker ---\n")

    rows = read_rows(FILE_NAME)
    new_id = generate_id()


    name = input("Customer Name: ")
    company = input("Company: ")
    phone = input("Phone Number: ")
    reason = input("Reason for call: ")

    print("\nStatus options:")
    for key, label in STATUSES.items():
        print(f"{key}. {label}")

    status_choice = input("Select status (1-4): ")
    status = STATUSES.get(status_choice, "Open")

    row = [
        new_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        name,
        company,
        phone,
        reason,
        status
    ]

    file_exists = FILE_NAME.exists()
    with FILE_NAME.open("a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(HEADERS)

        writer.writerow(row)

    # 🔗 ALSO update contacts automatically
    add_contact(name, company, phone)

    print("\n✅ Call logged successfully!")
    pause()

def generate_id():
    rows = read_rows(FILE_NAME)

    if len(rows) <= 1:
        return 1

    ids = []

    for row in rows[1:]:
        try:
            ids.append(int(row[0]))
        except (ValueError, IndexError):
            pass

    return max(ids) + 1 if ids else 1

def view_calls():
    print("\n--- OPEN CALLS (WORK QUEUE) ---\n")

    rows = read_rows(FILE_NAME)
    if not rows:
        print("No calls logged yet.")
        pause()
        return

    print(HEADERS)
    open_calls = [row for row in rows[1:] if row and row[-1] == "Open"]

    if open_calls:
        for row in open_calls:
            print(
    f"ID: {row[0]} | "
    f"Time: {row[1]} | "
    f"Name: {row[2]} | "
    f"Company: {row[3]} | "
    f"Phone: {row[4]} | "
    f"Reason: {row[5]} | "
    f"Status: {row[6]}"         
)
    else:
        print("No open calls 🎉")

    pause()


def search_call():
    print("\n--- SEARCH CALLS ---\n")

    query = input("Search by name, phone, company, or reason: ").lower().strip()

    rows = read_rows(FILE_NAME)

    if not rows:
        print("No calls logged yet.")
        pause()
        return

    matches = []

    for row in rows[1:]:
        if not row or len(row) < 2:
            continue

        # Combine searchable fields
        searchable_text = " ".join(row).lower()

        if query in searchable_text:
            matches.append(row)

    if matches:
        for row in matches:
            print(
                f"ID: {row[0]} | "
                f"Time: {row[1]} | "
                f"Name: {row[2]} | "
                f"Company: {row[3]} | "
                f"Phone: {row[4]} | "
                f"Reason: {row[5]} | "
                f"Status: {row[6]}"
            )
    else:
        print("No matching calls found.")

    pause()

def search_contacts():
    print("\n--- SEARCH CONTACTS ---\n")

    query = input(
        "Search by name, company, or phone: "
    ).lower().strip()

    contacts = read_contacts()

    matches = []

    for row in contacts[1:]:
        searchable = " ".join(row).lower()

        if query in searchable:
            matches.append(row)

    if matches:
        for row in matches:
            print(
                f"Name: {row[0]} | "
                f"Company: {row[1]} | "
                f"Phone: {row[2]}"
            )
    else:
        print("No matching contacts found.")

    pause()

def search_rows(query: str):
    rows = read_rows(FILE_NAME)

    matches = []

    for row in rows[1:]:
        if not row or len(row) < 2:
            continue

        searchable_text = " ".join(row).lower()

        if query in searchable_text:
            matches.append(row)

    return matches

def edit_call():
    print("\n--- EDIT CALL ---\n")

    query = input("Search call (name, phone, company, reason): ").lower().strip()

    matches = search_rows(query)

    if not matches:
        print("\nNo matching calls found.")
        pause()
        return

    print("\nMatching Calls:\n")

    for i, row in enumerate(matches, start=1):
        print(f"{i}. ID:{row[0]} | {row[2]} | {row[3]} | {row[-1]}")

    choice = input("\nSelect a call to edit: ")

    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(matches):
        print("\nInvalid selection.")
        pause()
        return

    selected = matches[int(choice) - 1]

    rows = read_rows(FILE_NAME)

    target_id = selected[0]

    updated = False

    for row in rows:
        if not row or row[0] != target_id:
            continue

        print("\nSelected Call:")
        print(f"Name: {row[2]}")
        print(f"Company: {row[3]}")
        print(f"Phone: {row[4]}")
        print(f"Reason: {row[5]}")
        print(f"Status: {row[-1]}")

        print("\nWhat would you like to edit?")
        print("1. Name")
        print("2. Company")
        print("3. Phone")
        print("4. Reason")
        print("5. Status")
        print("6. Cancel")

        action = input("\nSelect option: ")

        if action == "1":
            row[2] = input("Enter new name: ")

        elif action == "2":
            row[3] = input("Enter new company: ")

        elif action == "3":
            row[4] = input("Enter new phone: ")

        elif action == "4":
            row[5] = input("Enter new reason: ")

        elif action == "5":
            print("\nStatus options:")
            for key, label in STATUSES.items():
                print(f"{key}. {label}")

            status_choice = input("Select status: ")
            row[-1] = STATUSES.get(status_choice, row[-1])

        elif action == "6":
            pause()
            return

        else:
            print("\nInvalid option.")
            pause()
            return

        updated = True

        # ---- CONTACT SYNC (THIS IS THE IMPORTANT PART) ----
        sync = input("\nUpdate contact phonebook too? (y/n): ").lower().strip()

        if sync == "y":
            update_contact(
                row[2],  # name
                row[3],  # company
                row[4]   # phone
            )

        break

    if updated:
        write_rows(rows)
        print("\n✅ Call updated!")
    else:
        print("\n⚠️ Call not found.")

    pause()

def edit_contact():
    print("\n--- EDIT CONTACT ---\n")

    query = input(
        "Search name, company, or phone: "
    ).lower().strip()

    contacts = read_contacts()

    matches = []

    for row in contacts[1:]:
        searchable = " ".join(row).lower()

        if query in searchable:
            matches.append(row)

    if not matches:
        print("No matching contacts found.")
        pause()
        return

    print("\nMatching Contacts:\n")

    for i, row in enumerate(matches, start=1):
        print(
            f"{i}. {row[0]} | "
            f"{row[1]} | "
            f"{row[2]}"
        )

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
    print("4. Cancel")

    action = input("\nSelect option: ")

    if action == "1":
        selected[0] = input("New name: ")

    elif action == "2":
        selected[1] = input("New company: ")

    elif action == "3":
        selected[2] = input("New phone: ")

    elif action == "4":
        return

    write_contacts(contacts)

    print("\n✅ Contact updated!")
    pause()

def mark_complete():
    print("\n--- MARK CALL AS COMPLETED ---\n")

    phone_search = input("Enter phone number to mark as completed: ")
    search_phone = normalize_phone(phone_search)

    rows = read_rows(FILE_NAME)

    if not rows:
        print("No calls logged yet.")
        pause()
        return

    found = False

    for row in rows:
        if row == HEADERS:
            continue

        if len(row) > 2:
            row_phone = normalize_phone(row[2])

            if row_phone == search_phone:
                row[-1] = "Completed"
                found = True

    write_rows(rows)

    if found:
        print("\n✅ Call marked as Completed!")
    else:
        print("\n⚠️ No matching call found.")

    pause()

def find_call_by_id(call_id):
    rows = read_rows(FILE_NAME)

    for row in rows:
        if row == HEADERS:
            continue

        if row and row[0] == str(call_id):
            return row

    return None

def add_contact(name, company, phone):
    rows = read_rows(CONTACT_FILE)

    # prevent duplicates by phone
    clean_phone = normalize_phone(phone)

    for row in rows:
        if row and normalize_phone(row[2]) == clean_phone:
            return  # already exists

    file_exists = CONTACT_FILE.exists()

    with CONTACT_FILE.open("a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(CONTACT_HEADERS)

        writer.writerow([name, company, phone])

def view_contacts():
    print("\n--- CONTACT LIST ---\n")

    contacts = read_contacts()

    if not contacts:
        print("No contacts found.")
        pause()
        return

    for row in contacts[1:]:
        if len(row) < 3:
            continue

        print(
            f"Name: {row[0]} | "
            f"Company: {row[1]} | "
            f"Phone: {row[2]}"
        )

    pause()

def open_queue():
    print("\n--- OPEN CALL QUEUE ---\n")

    rows = read_rows(FILE_NAME)

    if not rows:
        print("No calls logged yet.")
        pause()
        return

    open_calls = []

    for row in rows[1:]:
        if not row or len(row) < 2:
            continue

        status = row[-1]

        if status in ["Open", "In Progress"]:
            open_calls.append(row)

    if not open_calls:
        print("🎉 No active calls. Everything is cleared.")
        pause()
        return

    for row in open_calls:
        print(
            f"ID: {row[0]} | "
            f"Time: {row[1]} | "
            f"Name: {row[2]} | "
            f"Company: {row[3]} | "
            f"Phone: {row[4]} | "
            f"Reason: {row[5]} | "
            f"Status: {row[6]}"
        )

    pause()

def customer_history():
    print("\n--- CUSTOMER HISTORY ---\n")

    query = input(
        "Search by name, company, or phone: "
    ).lower().strip()

    rows = read_rows(FILE_NAME)

    if not rows:
        print("No calls logged yet.")
        pause()
        return

    matches = []

    for row in rows[1:]:
        searchable = " ".join(row).lower()

        if query in searchable:
            matches.append(row)

    if not matches:
        print("No matching history found.")
        pause()
        return

    print("\n--- HISTORY ---\n")

    for row in matches:
        print(f"Call ID: {row[0]}")
        print(f"Date: {row[1]}")
        print(f"Name: {row[2]}")
        print(f"Company: {row[3]}")
        print(f"Phone: {row[4]}")
        print(f"Reason: {row[5]}")
        print(f"Status: {row[6]}")
        print("-" * 40)

    pause()

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

def dashboard():
    print("\n--- CALL DASHBOARD ---\n")

    rows = read_rows(FILE_NAME)

    if not rows:
        print("No calls logged yet.")
        pause()
        return

    today_calls = 0
    open_count = 0
    progress_count = 0
    completed_count = 0
    lost_count = 0

    today = datetime.now().strftime("%Y-%m-%d")

    for row in rows[1:]:
        if not row or len(row) < 2:
            continue

        timestamp = row[1]
        status = row[-1]

        # TODAY filter
        if timestamp.startswith(today):
            today_calls += 1

        # STATUS counts
        if status == "Open":
            open_count += 1
        elif status == "In Progress":
            progress_count += 1
        elif status == "Completed":
            completed_count += 1
        elif status == "Lost":
            lost_count += 1

    total_calls = open_count + progress_count + completed_count + lost_count

    print(f"Today’s Calls: {today_calls}")
    print(f"Open: {open_count}")
    print(f"In Progress: {progress_count}")
    print(f"Completed: {completed_count}")
    print(f"Lost: {lost_count}")
    print("-" * 30)
    print(f"Total Calls: {total_calls}")

    pause()

def main():
    while True:
        print("\n--- Construction Call Menu ---\n")
        print("1. Log New Call")
        print("2. Open Queue")
        print("3. Search Calls")
        print("4. Edit Call")
        print("5. Dashboard")
        print("6. Contact Manager")
        print("7. Exit")    

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
            dashboard()
        elif choice == "6": 
            contact_manager()
        elif choice == "7":
            break
        else:
            print("\nInvalid choice — try again.")


if __name__ == "__main__":
    main()
