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


def write_rows(file_path, rows):
    with file_path.open("w", newline="") as file:
        csv.writer(file).writerows(rows)


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

    phone_search = input("Enter phone number to search: ")
    clean_search = normalize_phone(phone_search)

    rows = read_rows(FILE_NAME)
    if not rows:
        print("No calls logged yet.")
        pause()
        return

    matches = [
        row
        for row in rows[1:]
        if clean_search in normalize_phone("".join(row))
    ]

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

    rows = read_rows(CONTACT_FILE)

    if not rows:
        print("No contacts yet.")
        pause()
        return

    for row in rows:
        print(row)

    pause()


def main():
    while True:
        print("\n--- Construction Call Menu ---\n")
        print("1. Log new call")
        print("2. View open calls")
        print("3. Search calls")
        print("4. Mark call as completed")
        print("5. View contacts")
        print("6. Exit")

        choice = input("\nSelect option: ")

        if choice == "1":
            log_call()
        elif choice == "2":
            view_calls()
        elif choice == "3":
            search_call()
        elif choice == "4":
            mark_complete()
        elif choice == "5":
            view_contacts()
        elif choice == "6":
            break
        else:
            print("\nInvalid choice — try again.")


if __name__ == "__main__":
    main()
