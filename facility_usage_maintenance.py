import json
import os
import csv
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


APP_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_FOLDER, "facility_records.json")

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

        # Keep the user's own capitalization (e.g. "IT Lab", "PCR Lab")
        # instead of forcing .title(), which would mangle acronyms.
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

        # float() accepts "nan"/"inf" without raising ValueError, and NaN
        # comparisons are always False, so it would silently slip past the
        # range check below. Reject it explicitly.
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

    def __init__(self):
        self._records = {}
        self.load_warnings = []
        self._saved_next_ids = {}

        # Reset the counter in case a manager was created before (e.g. tests).
        FacilityRecord.next_id = 1

        self.load_file()
        self.update_next_id()

    def update_next_id(self):
        """Find unused IDs without reusing numbers saved in the counter file."""
        # Each id below is computed as max(highest_existing + 1, saved_value),
        # which is already guaranteed to be free — the old "bump until free"
        # while-loops that used to follow could never actually run and were
        # removed.
        highest_record_id = max(self._records.keys(), default=0)
        record_id = max(
            highest_record_id + 1,
            self._saved_next_ids.get("record", 1)
        )
        FacilityRecord.next_id = record_id

    def assign_new_id(self, record):
        """Assign an ID only after every input field has passed validation."""
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

            if isinstance(record, UsageLog):
                text += (
                    " " + record.user_name.lower() +
                    " " + record.purpose.lower() +
                    " " + str(record.duration).lower()
                )
            else:
                text += (
                    " " + record.technician.lower() +
                    " " + record.condition.lower() +
                    " " + record.maintenance_status.lower() +
                    " " + record.next_service.lower()
                )

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

    # SUMMARY
    def condition_summary(self):
        summary = {}

        for condition in CONDITIONS:
            summary[condition] = 0

        for record in self._records.values():
            if isinstance(record, MaintenanceRecord):
                summary[record.condition] += 1

        return summary

    def detailed_report(self):
        """Calculate usage and maintenance statistics for all records."""
        usage_count = 0
        maintenance_count = 0
        total_usage_hours = 0.0
        facility_usage = {}
        facility_types = {}
        maintenance_statuses = {}

        for facility_type in FACILITY_TYPES:
            facility_types[facility_type] = 0

        for status in MAINTENANCE_STATUS:
            maintenance_statuses[status] = 0

        for record in self._records.values():
            facility_types[record.facility_type] += 1

            if isinstance(record, UsageLog):
                usage_count += 1
                total_usage_hours += record.duration

                if record.facility_name not in facility_usage:
                    facility_usage[record.facility_name] = 0

                facility_usage[record.facility_name] += 1
            else:
                maintenance_count += 1
                maintenance_statuses[record.maintenance_status] += 1

        most_used_facility = "-"

        if facility_usage:
            highest_usage = max(facility_usage.values())
            most_used = []

            for facility_name, count in facility_usage.items():
                if count == highest_usage:
                    most_used.append(facility_name)

            most_used.sort()
            most_used_facility = (
                ", ".join(most_used) + f" ({highest_usage} usage log(s))"
            )

        return {
            "total_records": len(self._records),
            "usage_count": usage_count,
            "maintenance_count": maintenance_count,
            "total_usage_hours": total_usage_hours,
            "most_used_facility": most_used_facility,
            "facility_types": facility_types,
            "maintenance_statuses": maintenance_statuses
        }

    def maintenance_reminders(self, upcoming_days=30, today=None):
        """Return incomplete maintenance due today or within a date range."""
        if today is None:
            today = datetime.today().date()

        reminders = []

        for record in self._records.values():
            if not isinstance(record, MaintenanceRecord):
                continue

            if record.maintenance_status == "Completed":
                continue

            if record.next_service == "":
                continue

            service_date = datetime.strptime(
                record.next_service,
                "%Y-%m-%d"
            ).date()

            days_remaining = (service_date - today).days

            if days_remaining < 0:
                reminder = f"Overdue by {abs(days_remaining)} day(s)"
            elif days_remaining == 0:
                reminder = "Due Today"
            elif days_remaining <= upcoming_days:
                reminder = f"Due in {days_remaining} day(s)"
            else:
                continue

            reminders.append((service_date, record, reminder))

        reminders.sort(key=lambda item: (item[0], item[1].code()))
        return reminders

    # EXPORT
    def export_csv(self, path):
        try:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                # Each field gets its own column so the export can be used
                # directly for spreadsheet calculations (e.g. summing
                # Duration, filtering by Next Service) instead of needing
                # to be re-parsed out of a combined text column.
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

    def __init__(self, parent):
        super().__init__(parent, padding=10)

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
        ttk.Label(
            self,
            text="Facility Usage & Maintenance Management",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # Main buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=5)

        buttons = [
            ("Add Usage", self.add_usage_form),
            ("Add Maintenance", self.add_maintenance_form),
            ("Delete", self.delete_selected),
            ("Report", self.show_detailed_report),
            ("Maintenance Reminder", self.show_maintenance_reminders),
            ("Export CSV", self.export_csv)
        ]

        for text, command in buttons:
            ttk.Button(
                button_frame,
                text=text,
                command=command
            ).pack(side="left", padx=3)

        # Search
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

        # Record table
        columns = (
            "id", "type", "facility", "facility_type", "date",
            "person", "detail", "condition", "status"
        )

        self.tree = ttk.Treeview(
            self,
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
            self.tree.column(column, width=130)

        self.tree.pack(fill="both", expand=True, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.select_record)

        # Details
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

        # Only offer facility types that currently exist among the
        # records, computed fresh each time so deleted records don't
        # leave stale options in the list.
        used_types = sorted({
            record.facility_type for record in self.manager.get_all()
        })
        # If a previously-chosen facility type no longer has any records
        # (e.g. its last record was deleted), fall back to "All" instead
        # of keeping a selection that isn't in the dropdown anymore.
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
        self.create_form(
            "Add Usage Log",
            [
                ("Facility Name", None),
                ("Facility Type", FACILITY_TYPES),
                ("Date (YYYY-MM-DD)", None),
                ("User Name", None),
                ("Purpose", None),
                ("Duration (hours)", None),
                ("Remarks", None)
            ],
            self.manager.add_usage
        )

    def add_maintenance_form(self):
        self.create_form(
            "Add Maintenance Record",
            [
                ("Facility Name", None),
                ("Facility Type", FACILITY_TYPES),
                ("Date (YYYY-MM-DD)", None),
                ("Condition", CONDITIONS),
                ("Technician", None),
                ("Next Service Date (YYYY-MM-DD)", None),
                ("Maintenance Status", MAINTENANCE_STATUS),
                ("Remarks", None)
            ],
            self.manager.add_maintenance
        )

    def create_form(self, title, fields, save_function):
        window = tk.Toplevel(self)
        window.title(title)

        variables = []
        widgets = []
        for row, (label_text, choices) in enumerate(fields):
            ttk.Label(
                window,
                text=label_text
            ).grid(row=row, column=0, padx=10, pady=5, sticky="w")

            variable = tk.StringVar()

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

                if len(choices) > 0:
                    variable.set(choices[0])

            widget.grid(row=row, column=1, padx=10, pady=5)
            variables.append(variable)
            widgets.append(widget)

        def save():
            values = []

            for variable in variables:
                values.append(variable.get())

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

                error_message = str(error).lower()

                # Find which input is wrong
                if "facility name" in error_message:
                    wrong_index = 0

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

                elif "facility type" in error_message:
                    wrong_index = 1

                elif "next service" in error_message:
                    wrong_index = 5

                elif "maintenance status" in error_message:
                    wrong_index = 6

                else:
                    wrong_index = 0

                # Return cursor to wrong input
                widgets[wrong_index].focus_set()

                # Highlight existing wrong value
                if isinstance(widgets[wrong_index], ttk.Entry):
                    widgets[wrong_index].selection_range(0, tk.END)

        # Press Enter = Save
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

        # Press Enter = Save
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
            self.manager.delete(int(selected[0]))
            self.selected_record = None
            self.detail_var.set(
                "Select a record to view details."
            )
            self.refresh_table()

    # ------------------------------------------------------------
    # Report / Export
    # ------------------------------------------------------------
    def show_detailed_report(self):
        """Display complete usage, maintenance, and condition statistics."""
        report = self.manager.detailed_report()
        condition_counts = self.manager.condition_summary()

        lines = [
            "FACILITY USAGE & MAINTENANCE REPORT",
            "=" * 54,
            "",
            f"Total Records: {report['total_records']}",
            f"Total Usage Logs: {report['usage_count']}",
            f"Total Maintenance Records: {report['maintenance_count']}",
            f"Total Usage Hours: {report['total_usage_hours']:.2f}",
            f"Most-Used Facility: {report['most_used_facility']}",
            "",
            "FACILITY TYPE SUMMARY",
            "-" * 54
        ]

        for facility_type, count in report["facility_types"].items():
            lines.append(f"{facility_type}: {count}")

        lines.extend([
            "",
            "MAINTENANCE STATUS SUMMARY",
            "-" * 54
        ])

        for status, count in report["maintenance_statuses"].items():
            lines.append(f"{status}: {count}")

        lines.extend([
            "",
            "FACILITY CONDITION SUMMARY",
            "-" * 54
        ])

        for condition, count in condition_counts.items():
            lines.append(f"{condition}: {count}")

        window = tk.Toplevel(self)
        window.title("Report")
        window.geometry("620x650")
        window.transient(self.winfo_toplevel())

        report_text = tk.Text(
            window,
            wrap="word",
            font=("Courier New", 10),
            padx=12,
            pady=12
        )
        report_text.pack(fill="both", expand=True, padx=10, pady=10)
        report_text.insert("1.0", "\n".join(lines))
        report_text.configure(state="disabled")

        ttk.Button(
            window,
            text="Close",
            command=window.destroy
        ).pack(pady=(0, 10))

    def show_maintenance_reminders(self):
        """Display overdue and upcoming maintenance within 30 days."""
        reminders = self.manager.maintenance_reminders(upcoming_days=30)

        if not reminders:
            messagebox.showinfo(
                "Maintenance Reminder",
                "No overdue or upcoming maintenance within 30 days."
            )
            return

        window = tk.Toplevel(self)
        window.title("Maintenance Reminder")
        window.geometry("920x420")
        window.transient(self.winfo_toplevel())

        ttk.Label(
            window,
            text="Overdue and Upcoming Maintenance (Next 30 Days)",
            font=("Arial", 13, "bold")
        ).pack(pady=(12, 4))

        ttk.Label(
            window,
            text="Completed maintenance records are excluded."
        ).pack(pady=(0, 8))

        table_frame = ttk.Frame(window)
        table_frame.pack(fill="both", expand=True, padx=12, pady=5)

        columns = (
            "id", "facility", "facility_type",
            "next_service", "status", "reminder"
        )
        reminder_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=11
        )

        headings = (
            "ID", "Facility", "Facility Type",
            "Next Service", "Status", "Reminder"
        )
        widths = (90, 170, 130, 110, 130, 190)

        for column, heading, width in zip(columns, headings, widths):
            reminder_tree.heading(column, text=heading)
            reminder_tree.column(column, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=reminder_tree.yview
        )
        reminder_tree.configure(yscrollcommand=scrollbar.set)
        reminder_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        reminder_tree.tag_configure("overdue", foreground="#b00020")
        reminder_tree.tag_configure("today", foreground="#c05a00")

        for service_date, record, reminder in reminders:
            if reminder.startswith("Overdue"):
                tag = "overdue"
            elif reminder == "Due Today":
                tag = "today"
            else:
                tag = "upcoming"

            reminder_tree.insert(
                "",
                "end",
                values=(
                    record.code(),
                    record.facility_name,
                    record.facility_type,
                    service_date.isoformat(),
                    record.maintenance_status,
                    reminder
                ),
                tags=(tag,)
            )

        ttk.Button(
            window,
            text="Close",
            command=window.destroy
        ).pack(pady=10)

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
