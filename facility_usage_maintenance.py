import json
import os
import csv
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


APP_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_FOLDER, "facility_records.json")
FACILITY_FILE = os.path.join(APP_FOLDER, "facility_file.json")

CONDITIONS = ("Good", "Fair", "Poor", "Under Repair")
MAINTENANCE_STATUS = ("Not Required", "Scheduled", "Completed", "Overdue")
FACILITY_TYPES = ("Classroom", "Lecture Hall", "Lab", "Gym",
                  "Court", "Pool", "Field", "Equipment")

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_date(value, field_name="Date"):
    """Validate a real calendar date written as YYYY-MM-DD."""
    value = value.strip()

    if not DATE_PATTERN.fullmatch(value):
        raise InvalidRecordError(f"{field_name} must be YYYY-MM-DD.")

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise InvalidRecordError(f"{field_name} is not a valid calendar date.")

    return value

class InvalidRecordError(Exception):
    pass

def load_shared_facilities(usage_only=False):
    """Load facilities from the shared facility_file.json."""
    if not os.path.exists(FACILITY_FILE):
        raise InvalidRecordError(
            "Shared facility file (facility_file.json) was not found."
        )

    try:
        with open(FACILITY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

    except OSError:
        raise InvalidRecordError(
            "Cannot open the shared facility file."
        )

    except json.JSONDecodeError:
        raise InvalidRecordError(
            "The shared facility file contains invalid JSON."
        )

    if (
        not isinstance(data, dict)
        or not isinstance(data.get("records"), list)
    ):
        raise InvalidRecordError(
            "The shared facility file has an unsupported structure."
        )

    facilities = []

    for item in data["records"]:

        if not isinstance(item, dict):
            continue

        if item.get("type") != "Facility":
            continue

        name = str(
            item.get("resource_name", "")
        ).strip()

        facility_type = str(
            item.get("resource_type", "")
        ).strip()

        status = str(
            item.get("status", "")
        ).strip().title()

        if name == "" or facility_type == "":
            continue

        # Usage only allows Active facilities
        if usage_only and status != "Active":
            continue

        # Maintenance does not allow retired facilities
        if not usage_only and status == "Retired":
            continue

        facilities.append(item)

    return facilities

# ============================================================
# Parent Class
# ============================================================
class FacilityRecord:
    next_id = 1

    def __init__(self, facility_name, facility_type, date, remarks=""):
        self._record_id = None

        self.facility_name = facility_name
        self.facility_type = facility_type.strip()
        self.date = date
        self.remarks = remarks.strip()

        if self.facility_type not in FACILITY_TYPES:
            raise InvalidRecordError("Invalid facility type.")

    @property
    def record_id(self):
        return self._record_id

    @property
    def facility_name(self):
        return self._facility_name

    @facility_name.setter
    def facility_name(self, value):
        value = value.strip()

        if value == "":
            raise InvalidRecordError("Facility name cannot be empty.")

        # Keep original capitalization
        self._facility_name = value

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        validated_date = validate_date(value)
        record_date = datetime.strptime(
            validated_date,
            "%Y-%m-%d"
        ).date()

        if record_date > datetime.today().date():
            raise InvalidRecordError("Date cannot be later than today.")

        self._date = validated_date

    def record_type(self):
        return "Facility Record"

    def code(self):
        return f"REC{self.record_id:04d}"

    def to_dict(self):
        return {
            "type": self.record_type(),
            "record_id": self.record_id,
            "facility_name": self.facility_name,
            "facility_type": self.facility_type,
            "date": self.date,
            "remarks": self.remarks
        }


# ============================================================
# Child Class 1 - Usage Log
# ============================================================
class UsageLog(FacilityRecord):

    def __init__(self, facility_name, facility_type, date,
                 user_name, purpose, duration, remarks=""):

        super().__init__(facility_name, facility_type, date, remarks)

        if user_name.strip() == "":
            raise InvalidRecordError("User name cannot be empty.")

        if purpose.strip() == "":
            raise InvalidRecordError("Purpose cannot be empty.")

        try:
            duration = float(duration)
        except ValueError:
            raise InvalidRecordError("Duration must be a number.")

        # Reject NaN because it does not behave like a normal numeric value.
        if duration != duration:
            raise InvalidRecordError("Duration must be a number.")

        if duration <= 0 or duration > 24:
            raise InvalidRecordError("Duration must be between 0 and 24 hours.")

        self.user_name = user_name.strip()
        self.purpose = purpose.strip()
        self.duration = duration

    def record_type(self):
        return "Usage Log"

    def code(self):
        return f"USG{self.record_id:04d}"

    def to_dict(self):
        data = super().to_dict()

        data["user_name"] = self.user_name
        data["purpose"] = self.purpose
        data["duration"] = self.duration

        return data

# ============================================================
# Child Class 2 - Maintenance Record
# ============================================================
class MaintenanceRecord(FacilityRecord):

    def __init__(self, facility_name, facility_type, date,
                 condition, technician, next_service,
                 maintenance_status="Not Required", remarks=""):

        super().__init__(facility_name, facility_type, date, remarks)

        condition = condition.strip().title()
        maintenance_status = maintenance_status.strip().title()

        if condition not in CONDITIONS:
            raise InvalidRecordError("Invalid condition.")

        if maintenance_status not in MAINTENANCE_STATUS:
            raise InvalidRecordError("Invalid maintenance status.")

        if technician.strip() == "":
            raise InvalidRecordError("Technician cannot be empty.")

        if next_service.strip() != "":
            next_service = validate_date(
                next_service,
                "Next service date"
            )

            service_date = datetime.strptime(
                next_service,
                "%Y-%m-%d"
            ).date()
            record_date = datetime.strptime(
                self.date,
                "%Y-%m-%d"
            ).date()

            if service_date < record_date:
                raise InvalidRecordError(
                    "Next service date cannot be earlier than record date."
                )

        self.condition = condition
        self.technician = technician.strip()
        self.next_service = next_service.strip()
        self.maintenance_status = maintenance_status

    def record_type(self):
        return "Maintenance"

    def code(self):
        return f"MTN{self.record_id:04d}"

    def to_dict(self):
        data = super().to_dict()

        data["condition"] = self.condition
        data["technician"] = self.technician
        data["next_service"] = self.next_service
        data["maintenance_status"] = self.maintenance_status

        return data

# ============================================================
# Manager Class
# ============================================================
class FacilityManager:
    """
    Manage facility usage and maintenance records.
    Handles CRUD operations, searching, file storage and CSV export.
    """
    def __init__(self):
        self._records = {}
        self.load_warnings = []
        self._saved_next_ids = {}

        # Reset the counter in case a manager was created before (e.g. tests).
        FacilityRecord.next_id = 1

        self.load_file()
        self.update_next_id()

    def update_next_id(self):
        """Find the next unused record ID."""

        record_id = self._saved_next_ids.get("record", 1)

        while record_id in self._records:
            record_id += 1

        FacilityRecord.next_id = record_id

    def assign_new_id(self, record):
        """Assign the next unused record ID."""

        record._record_id = FacilityRecord.next_id
        FacilityRecord.next_id += 1

    # CREATE
    def add_usage(self, values):
        record = UsageLog(*values)
        old_next_id = FacilityRecord.next_id
        self.assign_new_id(record)
        self._records[record.record_id] = record

        try:
            self.save_file()
        except InvalidRecordError:
            del self._records[record.record_id]
            FacilityRecord.next_id = old_next_id
            raise

    def add_maintenance(self, values):
        record = MaintenanceRecord(*values)
        old_next_id = FacilityRecord.next_id
        self.assign_new_id(record)
        self._records[record.record_id] = record

        try:
            self.save_file()
        except InvalidRecordError:
            del self._records[record.record_id]
            FacilityRecord.next_id = old_next_id
            raise

    # READ
    def get_all(self):
        return list(self._records.values())

    def get(self, record_id):
        return self._records.get(record_id)

    def search(self, keyword):
        keyword = keyword.strip().lower()

        if keyword == "":
            return self.get_all()

        result = []

        for record in self._records.values():
            text = (
                record.code() + " " +
                record.facility_name + " " +
                record.facility_type + " " +
                record.date + " " +
                record.remarks
            ).lower()

            match record.record_type():

                case "Usage Log":
                    text += (
                        " " + record.user_name.lower() +
                        " " + record.purpose.lower() +
                        " " + str(record.duration).lower()
                    )

                case "Maintenance":
                    text += (
                        " " + record.technician.lower() +
                        " " + record.condition.lower() +
                        " " + record.maintenance_status.lower() +
                        " " + record.next_service.lower()
                    )

                case _:
                    pass

            if keyword in text:
                result.append(record)

        return result

    def filter_type(self, records, record_type):
        if record_type == "All":
            return records

        result = []

        for record in records:
            if record.record_type() == record_type:
                result.append(record)

        return result

    # UPDATE
    def update_record(self, record_id, values):
        """Update every field of the selected record."""
        old_record = self.get(record_id)

        if old_record is None:
            raise InvalidRecordError("Record not found.")

        # Reuse the class constructors so all validation is checked again.
        if isinstance(old_record, UsageLog):
            updated_record = UsageLog(*values)
        else:
            updated_record = MaintenanceRecord(*values)

        # Keep the original record ID after editing.
        updated_record._record_id = record_id
        self._records[record_id] = updated_record

        try:
            self.save_file()
        except InvalidRecordError:
            self._records[record_id] = old_record
            raise

    # DELETE
    def delete(self, record_id):
        if record_id in self._records:
            deleted_record = self._records.pop(record_id)

            try:
                self.save_file()
            except InvalidRecordError:
                self._records[record_id] = deleted_record
                raise
        else:
            raise InvalidRecordError("Record not found.")

    # FILE PROCESSING
    def save_file(self):
        records = []

        for record in self._records.values():
            records.append(record.to_dict())

        data = {
            "next_ids": {
                "record": FacilityRecord.next_id
            },
            "records": records
        }

        temporary_file = DATA_FILE + ".tmp"

        try:
            with open(temporary_file, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
            os.replace(temporary_file, DATA_FILE)
        except OSError:
            if os.path.exists(temporary_file):
                try:
                    os.remove(temporary_file)
                except OSError:
                    pass
            raise InvalidRecordError("Cannot save file.")

    def load_file(self):
        if not os.path.exists(DATA_FILE):
            return

        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
        except OSError:
            self.load_warnings.append("The data file could not be opened.")
            return
        except json.JSONDecodeError:
            self.load_warnings.append(
                "The data file contains invalid JSON and could not be loaded."
            )
            return

        if isinstance(data, list):
            # Compatibility with files produced by earlier versions.
            items = data
        elif isinstance(data, dict) and isinstance(data.get("records"), list):
            items = data["records"]
            next_ids = data.get("next_ids", {})

            if isinstance(next_ids, dict):
                value = next_ids.get("record")
                if isinstance(value, int) and value > 0:
                    self._saved_next_ids["record"] = value
        else:
            self.load_warnings.append(
                "The data file has an unsupported structure. No records were loaded."
            )
            return

        for position, item in enumerate(items, start=1):
            try:
                if not isinstance(item, dict):
                    raise InvalidRecordError("Record is not a JSON object.")

                if item["type"] == "Usage Log":
                    record = UsageLog(
                        item["facility_name"],
                        item["facility_type"],
                        item["date"],
                        item["user_name"],
                        item["purpose"],
                        item["duration"],
                        item.get("remarks", "")
                    )
                elif item["type"] == "Maintenance":
                    record = MaintenanceRecord(
                        item["facility_name"],
                        item["facility_type"],
                        item["date"],
                        item["condition"],
                        item["technician"],
                        item.get("next_service", ""),
                        item.get("maintenance_status", "Not Required"),
                        item.get("remarks", "")
                    )
                else:
                    raise InvalidRecordError(
                        f"Unknown record type: {item.get('type', '-')}."
                    )

                record_id = item["record_id"]
                if not isinstance(record_id, int) or record_id <= 0:
                    raise InvalidRecordError("Record ID must be a positive integer.")
                if record_id in self._records:
                    raise InvalidRecordError("Duplicate record ID.")

                record._record_id = record_id
                self._records[record.record_id] = record

            except (KeyError, TypeError, ValueError,
                    AttributeError, InvalidRecordError) as error:
                self.load_warnings.append(
                    f"Record {position} was skipped: {error}"
                )
                continue

        # next ID will be recalculated by update_next_id()

    # EXPORT
    def export_csv(self, path):
        try:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                writer.writerow([
                    "ID", "Type", "Facility", "Facility Type", "Date",
                    "User/Technician", "Purpose", "Duration (hours)",
                    "Condition", "Maintenance Status", "Next Service",
                    "Remarks"
                ])

                for record in self._records.values():
                    if isinstance(record, UsageLog):
                        person = record.user_name
                        purpose = record.purpose
                        duration = record.duration
                        condition = ""
                        status = ""
                        next_service = ""
                    else:
                        person = record.technician
                        purpose = ""
                        duration = ""
                        condition = record.condition
                        status = record.maintenance_status
                        next_service = record.next_service

                    writer.writerow([
                        record.code(),
                        record.record_type(),
                        record.facility_name,
                        record.facility_type,
                        record.date,
                        person,
                        purpose,
                        duration,
                        condition,
                        status,
                        next_service,
                        record.remarks
                    ])

        except OSError:
            raise InvalidRecordError("Cannot export CSV.")

# ============================================================
# GUI
# ============================================================
class FacilityUsageMaintenanceFrame(ttk.Frame):

    def __init__(self, parent, back_command=None):
        super().__init__(parent, padding=10)
        self.back_command = back_command

        self.manager = FacilityManager()
        self.selected_record = None

        # Store the current choices from the filter window.
        self.filter_type_var = tk.StringVar(value="All")
        self.filter_facility_var = tk.StringVar(value="All")
        self.filter_condition_var = tk.StringVar(value="All")
        self.filter_status_var = tk.StringVar(value="All")
        self.sort_reverse = {}
        self.column_headings = {}

        self.create_widgets()
        self.refresh_table()

        if self.manager.load_warnings:
            warning_text = "\n".join(self.manager.load_warnings)
            self.after_idle(
                lambda: messagebox.showwarning(
                    "Data File Warning",
                    warning_text
                )
            )

    def create_widgets(self):
        title_frame = ttk.Frame(self)
        title_frame.pack(fill="x", pady=10)

        if self.back_command:
            tk.Button(
                title_frame,
                text="← Back",
                font=("Microsoft YaHei UI Light", 10),
                command=self.back_command
            ).pack(side="left", padx=(5, 20))

        tk.Label(
            title_frame,
            text="Facility Usage & Maintenance Management",
            fg="#57a1f8",
            bg="white",
            font=("Microsoft YaHei UI Light", 14, "bold")
        ).pack(side="top")

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=5)
        
        buttons = [
            ("Add Usage", self.add_usage_form),
            ("Add Maintenance", self.add_maintenance_form),
            ("Delete", self.delete_selected),
            ("Export CSV", self.export_csv)
        ]

        for text, command in buttons:
            ttk.Button(
                button_frame,
                text=text,
                command=command
            ).pack(side="left", padx=3)

        search_frame = ttk.Frame(self)
        search_frame.pack(fill="x", pady=8)

        ttk.Label(search_frame, text="Search:").pack(side="left")

        self.search_var = tk.StringVar()

        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=25
        )
        search_entry.pack(side="left", padx=5)

        search_entry.bind(
            "<Return>",
            lambda event: self.apply_filter()
        )

        ttk.Button(
            search_frame,
            text="Filter",
            command=self.open_filter_window
        ).pack(side="left", padx=5)

        self.filter_summary_var = tk.StringVar(value="Filters: All")
        ttk.Label(
            search_frame,
            textvariable=self.filter_summary_var
        ).pack(side="left", padx=5)

        ttk.Button(
            search_frame,
            text="Search",
            command=self.apply_filter
        ).pack(side="left", padx=3)

        ttk.Button(
            search_frame,
            text="Refresh",
            command=self.refresh_table
        ).pack(side="left", padx=3)

        columns = (
            "id", "type", "facility", "facility_type", "date",
            "person", "detail", "condition", "status"
        )

        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, pady=5)

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=13
        )

        headings = (
            "ID", "Type", "Facility", "Facility Type", "Date",
            "User / Technician", "Purpose / Detail",
            "Condition", "Maintenance Status"
        )

        for column, heading in zip(columns, headings):
            self.column_headings[column] = heading

            self.tree.heading(
                column,
                text=heading,
                command=lambda selected_column=column:
                    self.sort_table(selected_column)
            )

            self.tree.column(
                column,
                width=130
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.select_record
        )
        
        detail_box = ttk.LabelFrame(self, text="Selected Record")
        detail_box.pack(fill="x", pady=8)

        self.detail_var = tk.StringVar(
            value="Select a record to view details."
        )

        ttk.Label(
            detail_box,
            textvariable=self.detail_var,
            wraplength=1000
        ).pack(anchor="w", padx=10, pady=8)

        update_frame = ttk.Frame(detail_box)
        update_frame.pack(anchor="w", padx=10, pady=(0, 8))

        ttk.Button(
            update_frame,
            text="Edit Selected",
            command=self.edit_selected
        ).pack(side="left", padx=3)

    # ------------------------------------------------------------
    # Table
    # ------------------------------------------------------------
    def refresh_table(self):
        self.search_var.set("")
        self.clear_filter_values()
        self.show_records(self.manager.get_all())

    def clear_filter_values(self):
        """Reset all choices in the filter window."""
        self.filter_type_var.set("All")
        self.filter_facility_var.set("All")
        self.filter_condition_var.set("All")
        self.filter_status_var.set("All")
        self.filter_summary_var.set("Filters: All")

    def open_filter_window(self):
        """Open a separate window containing all record filters."""
        window = tk.Toplevel(self)
        window.title("Filter Records")
        window.resizable(False, False)
        window.transient(self.winfo_toplevel())
        window.grab_set()

        # Use temporary variables so Cancel discards every change.
        type_var = tk.StringVar(value=self.filter_type_var.get())
        facility_var = tk.StringVar(value=self.filter_facility_var.get())
        condition_var = tk.StringVar(value=self.filter_condition_var.get())
        status_var = tk.StringVar(value=self.filter_status_var.get())

        ttk.Label(
            window,
            text="Filter Records",
            font=("Arial", 13, "bold")
        ).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10))

        labels = (
            "Filter Type",
            "Facility Type",
            "Condition",
            "Maintenance Status"
        )

        for row, text in enumerate(labels, start=1):
            ttk.Label(window, text=text + ":").grid(
                row=row, column=0, padx=15, pady=6, sticky="w"
            )

        type_combo = ttk.Combobox(
            window,
            textvariable=type_var,
            values=("All", "Usage Log", "Maintenance"),
            state="readonly",
            width=24
        )
        type_combo.grid(row=1, column=1, padx=15, pady=6)

        # Show only facility types that currently have records.
        used_types = sorted({
            record.facility_type for record in self.manager.get_all()
        })
        # Reset invalid previous selections.
        if facility_var.get() not in used_types:
            facility_var.set("All")

        facility_combo = ttk.Combobox(
            window,
            textvariable=facility_var,
            values=("All",) + tuple(used_types),
            state="readonly",
            width=24
        )
        facility_combo.grid(row=2, column=1, padx=15, pady=6)

        condition_combo = ttk.Combobox(
            window,
            textvariable=condition_var,
            values=("All",) + CONDITIONS,
            state="readonly",
            width=24
        )
        condition_combo.grid(row=3, column=1, padx=15, pady=6)

        status_combo = ttk.Combobox(
            window,
            textvariable=status_var,
            values=("All",) + MAINTENANCE_STATUS,
            state="readonly",
            width=24
        )
        status_combo.grid(row=4, column=1, padx=15, pady=6)

        def update_filter_states(event=None):
            if type_var.get() == "Usage Log":
                condition_var.set("All")
                status_var.set("All")
                condition_combo.configure(state="disabled")
                status_combo.configure(state="disabled")
            else:
                condition_combo.configure(state="readonly")
                status_combo.configure(state="readonly")

        def apply_and_close():
            self.filter_type_var.set(type_var.get())
            self.filter_facility_var.set(facility_var.get())
            self.filter_condition_var.set(condition_var.get())
            self.filter_status_var.set(status_var.get())
            self.apply_filter()
            window.destroy()

        def clear_and_close():
            self.clear_filter_values()
            self.apply_filter()
            window.destroy()

        type_combo.bind("<<ComboboxSelected>>", update_filter_states)
        update_filter_states()

        button_frame = ttk.Frame(window)
        button_frame.grid(row=5, column=0, columnspan=2, pady=15)

        ttk.Button(
            button_frame,
            text="Apply Filter",
            command=apply_and_close
        ).pack(side="left", padx=4)

        ttk.Button(
            button_frame,
            text="Clear Filters",
            command=clear_and_close
        ).pack(side="left", padx=4)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=window.destroy
        ).pack(side="left", padx=4)

        window.bind("<Return>", lambda event: apply_and_close())
        type_combo.focus_set()

    def apply_filter(self):
        records = self.manager.search(
            self.search_var.get()
        )

        records = self.manager.filter_type(
            records,
            self.filter_type_var.get()
        )

        facility_type = self.filter_facility_var.get()
        condition = self.filter_condition_var.get()
        status = self.filter_status_var.get()

        if facility_type != "All":
            records = [
                record for record in records
                if record.facility_type == facility_type
            ]

        if condition != "All":
            records = [
                record for record in records
                if isinstance(record, MaintenanceRecord)
                and record.condition == condition
            ]

        if status != "All":
            records = [
                record for record in records
                if isinstance(record, MaintenanceRecord)
                and record.maintenance_status == status
            ]

        active_filters = []
        for name, value in (
            ("Type", self.filter_type_var.get()),
            ("Facility", facility_type),
            ("Condition", condition),
            ("Status", status)
        ):
            if value != "All":
                active_filters.append(f"{name}: {value}")

        if active_filters:
            self.filter_summary_var.set(
                "Filters: " + " | ".join(active_filters)
            )
        else:
            self.filter_summary_var.set("Filters: All")

        self.show_records(records)

    def show_records(self, records):
        self.selected_record = None
        self.detail_var.set("Select a record to view details.")
        self.sort_reverse.clear()

        for column, heading in self.column_headings.items():
            self.tree.heading(column, text=heading)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for record in records:
            if isinstance(record, UsageLog):
                person = record.user_name
                detail = f"{record.duration}h - {record.purpose}"
                condition = "-"
                status = "-"
            else:
                person = record.technician
                detail = f"Next: {record.next_service or '-'}"
                condition = record.condition
                status = record.maintenance_status

            self.tree.insert(
                "",
                "end",
                iid=str(record.record_id),
                values=(
                    record.code(),
                    record.record_type(),
                    record.facility_name,
                    record.facility_type,
                    record.date,
                    person,
                    detail,
                    condition,
                    status
                )
            )

    def sort_table(self, column):
        """Sort visible table rows when a column heading is clicked."""
        reverse = self.sort_reverse.get(column, False)
        rows = []

        for item in self.tree.get_children(""):
            value = self.tree.set(item, column).strip()

            if column == "id":
                match = re.fullmatch(r"([A-Z]+)(\d+)", value)
                if match:
                    sort_value = (match.group(1), int(match.group(2)))
                else:
                    sort_value = (value.lower(), 0)
            elif column == "detail":
                number_match = re.match(r"^(\d+(?:\.\d+)?)", value)
                if number_match:
                    sort_value = (0, float(number_match.group(1)))
                else:
                    sort_value = (1, value.lower())
            else:
                sort_value = value.lower()

            rows.append((sort_value, item))

        rows.sort(key=lambda row: row[0], reverse=reverse)

        for position, (_, item) in enumerate(rows):
            self.tree.move(item, "", position)

        for name, heading in self.column_headings.items():
            self.tree.heading(name, text=heading)

        arrow = "▼" if reverse else "▲"
        self.tree.heading(
            column,
            text=f"{self.column_headings[column]} {arrow}"
        )
        self.sort_reverse[column] = not reverse

    def select_record(self, event=None):
        selected = self.tree.selection()

        if not selected:
            return

        record = self.manager.get(int(selected[0]))
        self.selected_record = record

        if isinstance(record, UsageLog):
            text = (
                f"{record.code()} | {record.facility_name} | "
                f"{record.facility_type} | {record.date} | "
                f"User: {record.user_name} | "
                f"Purpose: {record.purpose} | "
                f"Duration: {record.duration}h | "
                f"Remarks: {record.remarks or '-'}"
            )
        else:
            text = (
                f"{record.code()} | {record.facility_name} | "
                f"{record.facility_type} | {record.date} | "
                f"Technician: {record.technician or '-'} | "
                f"Condition: {record.condition} | "
                f"Status: {record.maintenance_status} | "
                f"Next Service: {record.next_service or '-'} | "
                f"Remarks: {record.remarks or '-'}"
            )

        self.detail_var.set(text)

    # ------------------------------------------------------------
    # Add Forms
    # ------------------------------------------------------------
    def add_usage_form(self):
        try:
            facilities = load_shared_facilities(
                usage_only=True
            )

        except InvalidRecordError as error:
            messagebox.showerror(
                "Facility File Error",
                str(error)
            )
            return

        if not facilities:
            messagebox.showwarning(
                "No Active Facility",
                "No active facility is available."
            )
            return

        self.create_form(
            "Add Usage Log",
            [
                ("Facility Name", None),
                ("Facility Type", None),
                ("Date (YYYY-MM-DD)", None),
                ("User Name", None),
                ("Purpose", None),
                ("Duration (hours)", None),
                ("Remarks", None)
            ],
            self.manager.add_usage,
            shared_facilities=facilities
        )


    def add_maintenance_form(self):

        try:
            facilities = load_shared_facilities(
                usage_only=False
            )

        except InvalidRecordError as error:
            messagebox.showerror(
                "Facility File Error",
                str(error)
            )
            return

        if not facilities:
            messagebox.showwarning(
                "No Facility",
                "No facility is available for maintenance."
            )
            return

        self.create_form(
            "Add Maintenance Record",
            [
                ("Facility Name", None),
                ("Facility Type", None),
                ("Date (YYYY-MM-DD)", None),
                ("Condition", CONDITIONS),
                ("Technician", None),
                ("Next Service Date (YYYY-MM-DD)", None),
                ("Maintenance Status", MAINTENANCE_STATUS),
                ("Remarks", None)
            ],
            self.manager.add_maintenance,
            shared_facilities=facilities
        )

    def create_form(
        self,
        title,
        fields,
        save_function,
        shared_facilities=None
    ):
        window = tk.Toplevel(self)
        window.title(title)

        variables = []
        widgets = []

        facility_lookup = {}

        if shared_facilities is not None:
            facility_lookup = {
                item["resource_name"]: item
                for item in shared_facilities
                if item.get("resource_name")
            }

        for row, (label_text, choices) in enumerate(fields):

            ttk.Label(
                window,
                text=label_text
            ).grid(
                row=row,
                column=0,
                padx=10,
                pady=5,
                sticky="w"
            )

            variable = tk.StringVar()

            # Facility Name
            if shared_facilities is not None and row == 0:

                facility_names = tuple(
                    facility_lookup.keys()
                )

                widget = ttk.Combobox(
                    window,
                    textvariable=variable,
                    values=facility_names,
                    state="readonly",
                    width=25
                )

                if facility_names:
                    variable.set(
                        facility_names[0]
                    )

            # Facility Type - automatically filled
            elif shared_facilities is not None and row == 1:

                widget = ttk.Entry(
                    window,
                    textvariable=variable,
                    state="readonly",
                    width=28
                )

            elif choices is None:

                widget = ttk.Entry(
                    window,
                    textvariable=variable,
                    width=28
                )

            else:

                widget = ttk.Combobox(
                    window,
                    textvariable=variable,
                    values=choices,
                    state="readonly",
                    width=25
                )

                if len(choices) > 0:
                    variable.set(
                        choices[0]
                    )

            widget.grid(
                row=row,
                column=1,
                padx=10,
                pady=5
            )

            variables.append(variable)
            widgets.append(widget)

        if shared_facilities is not None and facility_lookup:

            def sync_facility_type(event=None):

                selected = facility_lookup.get(
                    variables[0].get()
                )

                if selected is None:
                    variables[1].set("")
                    return

                variables[1].set(
                    str(
                        selected.get(
                            "resource_type",
                            ""
                        )
                    ).strip()
                )

            widgets[0].bind(
                "<<ComboboxSelected>>",
                sync_facility_type
            )

            sync_facility_type()

        def save():
            values = []

            for variable in variables:
                values.append(
                    variable.get()
                )

            try:
                save_function(values)

                window.destroy()
                self.refresh_table()

                messagebox.showinfo(
                    "Success",
                    "Record saved successfully."
                )

            except InvalidRecordError as error:

                messagebox.showerror(
                    "Invalid Input",
                    str(error)
                )

                error_message = str(
                    error
                ).lower()

                if "facility name" in error_message:
                    wrong_index = 0

                elif (
                    "date" in error_message
                    and "next service" not in error_message
                ):
                    wrong_index = 2

                elif "user name" in error_message:
                    wrong_index = 3

                elif "purpose" in error_message:
                    wrong_index = 4

                elif "duration" in error_message:
                    wrong_index = 5

                elif "condition" in error_message:
                    wrong_index = 3

                elif "technician" in error_message:
                    wrong_index = 4

                elif "facility type" in error_message:
                    wrong_index = 1

                elif "next service" in error_message:
                    wrong_index = 5

                elif "maintenance status" in error_message:
                    wrong_index = 6

                else:
                    wrong_index = 0

                widgets[
                    wrong_index
                ].focus_set()

                if isinstance(
                    widgets[wrong_index],
                    ttk.Entry
                ):
                    widgets[
                        wrong_index
                    ].selection_range(
                        0,
                        tk.END
                    )

        window.bind(
            "<Return>",
            lambda event: save()
        )

        ttk.Button(
            window,
            text="Save",
            command=save
        ).grid(
            row=len(fields),
            column=0,
            columnspan=2,
            pady=10
        )
    # ------------------------------------------------------------
    # Update / Delete
    # ------------------------------------------------------------
    def edit_selected(self):
        """Edit all information of the selected record."""
        record = self.selected_record

        if record is None:
            messagebox.showinfo(
                "Select Record",
                "Please select a record first."
            )
            return

        window = tk.Toplevel(self)
        window.title("Edit Record")

        variables = []
        widgets = []

        if isinstance(record, UsageLog):
            fields = [
                ("Facility Name", None, record.facility_name),
                ("Facility Type", FACILITY_TYPES, record.facility_type),
                ("Date (YYYY-MM-DD)", None, record.date),
                ("User Name", None, record.user_name),
                ("Purpose", None, record.purpose),
                ("Duration (hours)", None, str(record.duration)),
                ("Remarks", None, record.remarks)
            ]
        else:
            fields = [
                ("Facility Name", None, record.facility_name),
                ("Facility Type", FACILITY_TYPES, record.facility_type),
                ("Date (YYYY-MM-DD)", None, record.date),
                ("Condition", CONDITIONS, record.condition),
                ("Technician", None, record.technician),
                ("Next Service Date (YYYY-MM-DD)", None, record.next_service),
                ("Maintenance Status",
                 MAINTENANCE_STATUS,
                 record.maintenance_status),
                ("Remarks", None, record.remarks)
            ]

        for row, (label_text, choices, current_value) in enumerate(fields):
            ttk.Label(
                window,
                text=label_text
            ).grid(
                row=row,
                column=0,
                padx=10,
                pady=5,
                sticky="w"
            )

            variable = tk.StringVar(value=current_value)

            if choices is None:
                widget = ttk.Entry(
                    window,
                    textvariable=variable,
                    width=28
                )
            else:
                widget = ttk.Combobox(
                    window,
                    textvariable=variable,
                    values=choices,
                    state="readonly",
                    width=25
                )

            widget.grid(
                row=row,
                column=1,
                padx=10,
                pady=5
            )

            variables.append(variable)
            widgets.append(widget)

        def save_changes():
            values = []

            for variable in variables:
                values.append(variable.get())

            try:
                self.manager.update_record(
                    record.record_id,
                    values
                )

                window.destroy()

                self.selected_record = None
                self.detail_var.set(
                    "Select a record to view details."
                )

                self.refresh_table()

                messagebox.showinfo(
                    "Success",
                    "Record updated successfully."
                )

            except InvalidRecordError as error:
                messagebox.showerror(
                    "Error",
                    str(error)
                )

                error_message = str(error).lower()

                if "facility name" in error_message:
                    wrong_index = 0
                elif "facility type" in error_message:
                    wrong_index = 1
                elif "date" in error_message and "next service" not in error_message:
                    wrong_index = 2
                elif "user name" in error_message:
                    wrong_index = 3
                elif "purpose" in error_message:
                    wrong_index = 4
                elif "duration" in error_message:
                    wrong_index = 5
                elif "condition" in error_message:
                    wrong_index = 3
                elif "technician" in error_message:
                    wrong_index = 4
                elif "next service" in error_message:
                    wrong_index = 5
                elif "maintenance status" in error_message:
                    wrong_index = 6
                else:
                    wrong_index = 0

                widgets[wrong_index].focus_set()

                if isinstance(widgets[wrong_index], ttk.Entry):
                    widgets[wrong_index].selection_range(0, tk.END)

        window.bind(
            "<Return>",
            lambda event: save_changes()
        )
        ttk.Button(
            window,
            text="Save Changes",
            command=save_changes
        ).grid(
            row=len(fields),
            column=0,
            columnspan=2,
            pady=10
        )

    def delete_selected(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                "Select Record",
                "Please select a record first."
            )
            return

        if messagebox.askyesno(
            "Delete",
            "Are you sure you want to delete this record?"
        ):
            try:
                self.manager.delete(int(selected[0]))

                self.selected_record = None
                self.detail_var.set(
                    "Select a record to view details."
                )
                self.refresh_table()

                messagebox.showinfo(
                    "Success",
                    "Record deleted successfully."
                )

            except InvalidRecordError as error:
                messagebox.showerror(
                    "Error",
                    str(error)
                )

    # ------------------------------------------------------------
    # Export
    # ------------------------------------------------------------
    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv")],
            initialfile="facility_records.csv"
        )

        if path == "":
            return

        try:
            self.manager.export_csv(path)
            messagebox.showinfo(
                "Success",
                "Records exported successfully."
            )
        except InvalidRecordError as error:
            messagebox.showerror("Error", str(error))

def main():
    root = tk.Tk()
    root.title("University Facilities Booking App")
    root.geometry("1280x650")

    page = FacilityUsageMaintenanceFrame(root)
    page.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
