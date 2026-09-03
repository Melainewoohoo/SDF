import json
import os
import csv
import re
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


APP_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(APP_FOLDER, "resource_records.json")

CONDITIONS = ("Good", "Fair", "Poor", "Under Repair")
STATUSES = ("Active", "Inactive", "Retired")
FACILITY_TYPES = ("Classroom", "Lecture Hall", "Lab", "Gym",
                  "Court", "Pool", "Field")
EQUIPMENT_TYPES = ("Projector", "Laptop", "Lab Instrument",
                   "Sports Equipment", "Other")

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


def validate_positive_int(value, field_name):
    """Validate a whole number greater than zero."""
    value = value.strip()

    try:
        number = int(value)
    except ValueError:
        raise InvalidRecordError(f"{field_name} must be a whole number.")

    if number <= 0:
        raise InvalidRecordError(f"{field_name} must be greater than zero.")

    return number


class InvalidRecordError(Exception):
    pass


# ============================================================
# Parent Class
# ============================================================
class ResourceRecord:
    next_id = 1

    def __init__(self, resource_name, resource_type, date_added,
                 condition, status, remarks=""):
        self._record_id = None

        self.resource_name = resource_name
        self.resource_type = resource_type.strip()
        self.date_added = date_added
        self.remarks = remarks.strip()

        condition = condition.strip().title()
        status = status.strip().title()

        if condition not in CONDITIONS:
            raise InvalidRecordError("Invalid condition.")

        if status not in STATUSES:
            raise InvalidRecordError("Invalid status.")

        self.condition = condition
        self.status = status

    @property
    def record_id(self):
        return self._record_id

    @property
    def resource_name(self):
        return self._resource_name

    @resource_name.setter
    def resource_name(self, value):
        value = value.strip()

        if value == "":
            raise InvalidRecordError("Resource name cannot be empty.")

        # Keep the user's own capitalization (e.g. "IT Lab", "PCR Lab")
        # instead of forcing .title(), which would mangle acronyms.
        self._resource_name = value

    @property
    def date_added(self):
        return self._date_added

    @date_added.setter
    def date_added(self, value):
        validated_date = validate_date(value, "Date added")
        record_date = datetime.strptime(
            validated_date,
            "%Y-%m-%d"
        ).date()

        if record_date > datetime.today().date():
            raise InvalidRecordError("Date added cannot be later than today.")

        self._date_added = validated_date

    def record_type(self):
        return "Resource Record"

    def code(self):
        return f"RES{self.record_id:04d}"

    def to_dict(self):
        return {
            "type": self.record_type(),
            "record_id": self.record_id,
            "resource_name": self.resource_name,
            "resource_type": self.resource_type,
            "date_added": self.date_added,
            "condition": self.condition,
            "status": self.status,
            "remarks": self.remarks
        }


# ============================================================
# Child Class 1 - Facility
# ============================================================
class Facility(ResourceRecord):

    def __init__(self, resource_name, resource_type, date_added,
                 location, capacity, condition, status, remarks=""):

        super().__init__(resource_name, resource_type, date_added,
                         condition, status, remarks)

        if resource_type.strip() not in FACILITY_TYPES:
            raise InvalidRecordError("Invalid facility type.")

        if location.strip() == "":
            raise InvalidRecordError("Location cannot be empty.")

        self.location = location.strip()
        self.capacity = validate_positive_int(capacity, "Capacity")

    def record_type(self):
        return "Facility"

    def code(self):
        return f"FAC{self.record_id:04d}"

    def to_dict(self):
        data = super().to_dict()

        data["location"] = self.location
        data["capacity"] = self.capacity

        return data


# ============================================================
# Child Class 2 - Equipment
# ============================================================
class Equipment(ResourceRecord):

    def __init__(self, resource_name, resource_type, date_added,
                 serial_number, quantity, condition, status, remarks=""):

        super().__init__(resource_name, resource_type, date_added,
                         condition, status, remarks)

        if resource_type.strip() not in EQUIPMENT_TYPES:
            raise InvalidRecordError("Invalid equipment type.")

        self.serial_number = serial_number.strip()
        self.quantity = validate_positive_int(quantity, "Quantity")

    def record_type(self):
        return "Equipment"

    def code(self):
        return f"EQP{self.record_id:04d}"

    def to_dict(self):
        data = super().to_dict()

        data["serial_number"] = self.serial_number
        data["quantity"] = self.quantity

        return data


# ============================================================
# Manager Class
# ============================================================
class ResourceManager:

    def __init__(self):
        self._records = {}
        self.load_warnings = []
        self._saved_next_ids = {}

        # Reset the counter in case a manager was created before (e.g. tests).
        ResourceRecord.next_id = 1

        self.load_file()
        self.update_next_id()

    def update_next_id(self):
        """Find unused IDs without reusing numbers saved in the counter file."""
        highest_record_id = max(self._records.keys(), default=0)
        record_id = max(
            highest_record_id + 1,
            self._saved_next_ids.get("record", 1)
        )
        ResourceRecord.next_id = record_id

    def assign_new_id(self, record):
        """Assign an ID only after every input field has passed validation."""
        record._record_id = ResourceRecord.next_id
        ResourceRecord.next_id += 1

    # CREATE
    def add_facility(self, values):
        record = Facility(*values)
        old_next_id = ResourceRecord.next_id
        self.assign_new_id(record)
        self._records[record.record_id] = record

        try:
            self.save_file()
        except InvalidRecordError:
            del self._records[record.record_id]
            ResourceRecord.next_id = old_next_id
            raise

    def add_equipment(self, values):
        record = Equipment(*values)
        old_next_id = ResourceRecord.next_id
        self.assign_new_id(record)
        self._records[record.record_id] = record

        try:
            self.save_file()
        except InvalidRecordError:
            del self._records[record.record_id]
            ResourceRecord.next_id = old_next_id
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
                record.resource_name + " " +
                record.resource_type + " " +
                record.date_added + " " +
                record.condition + " " +
                record.status + " " +
                record.remarks
            ).lower()

            if isinstance(record, Facility):
                text += (
                    " " + record.location.lower() +
                    " " + str(record.capacity).lower()
                )
            else:
                text += (
                    " " + record.serial_number.lower() +
                    " " + str(record.quantity).lower()
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
        if isinstance(old_record, Facility):
            updated_record = Facility(*values)
        else:
            updated_record = Equipment(*values)

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
                "record": ResourceRecord.next_id
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

                if item["type"] == "Facility":
                    record = Facility(
                        item["resource_name"],
                        item["resource_type"],
                        item["date_added"],
                        item["location"],
                        item["capacity"],
                        item["condition"],
                        item["status"],
                        item.get("remarks", "")
                    )
                elif item["type"] == "Equipment":
                    record = Equipment(
                        item["resource_name"],
                        item["resource_type"],
                        item["date_added"],
                        item["serial_number"],
                        item["quantity"],
                        item["condition"],
                        item["status"],
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
            summary[record.condition] += 1

        return summary

    def status_summary(self):
        summary = {}

        for status in STATUSES:
            summary[status] = 0

        for record in self._records.values():
            summary[record.status] += 1

        return summary

    def detailed_report(self):
        """Calculate facility and equipment inventory statistics."""
        facility_count = 0
        equipment_count = 0
        total_capacity = 0
        total_quantity = 0
        resource_types = {}

        for resource_type in FACILITY_TYPES + EQUIPMENT_TYPES:
            resource_types[resource_type] = 0

        for record in self._records.values():
            resource_types[record.resource_type] += 1

            if isinstance(record, Facility):
                facility_count += 1
                total_capacity += record.capacity
            else:
                equipment_count += 1
                total_quantity += record.quantity

        return {
            "total_records": len(self._records),
            "facility_count": facility_count,
            "equipment_count": equipment_count,
            "total_capacity": total_capacity,
            "total_quantity": total_quantity,
            "resource_types": resource_types
        }

    # EXPORT
    def export_csv(self, path):
        try:
            with open(path, "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                # Each field gets its own column so the export can be used
                # directly for spreadsheet calculations (e.g. summing
                # Capacity/Quantity, filtering by Status) instead of needing
                # to be re-parsed out of a combined text column.
                writer.writerow([
                    "ID", "Type", "Resource Name", "Resource Type",
                    "Date Added", "Location/Serial", "Capacity/Quantity",
                    "Condition", "Status", "Remarks"
                ])

                for record in self._records.values():
                    if isinstance(record, Facility):
                        location_or_serial = record.location
                        capacity_or_quantity = record.capacity
                    else:
                        location_or_serial = record.serial_number
                        capacity_or_quantity = record.quantity

                    writer.writerow([
                        record.code(),
                        record.record_type(),
                        record.resource_name,
                        record.resource_type,
                        record.date_added,
                        location_or_serial,
                        capacity_or_quantity,
                        record.condition,
                        record.status,
                        record.remarks
                    ])

        except OSError:
            raise InvalidRecordError("Cannot export CSV.")


# ============================================================
# GUI
# ============================================================
class FacilityResourceManagementFrame(ttk.Frame):

    def __init__(self, parent):
        super().__init__(parent, padding=10)

        self.manager = ResourceManager()
        self.selected_record = None

        # Store the current choices from the filter window.
        self.filter_type_var = tk.StringVar(value="All")
        self.filter_resource_type_var = tk.StringVar(value="All")
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
        ttk.Label(
            self,
            text="Facility & Resource Management",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # Main buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", pady=5)

        buttons = [
            ("Add Facility", self.add_facility_form),
            ("Add Equipment", self.add_equipment_form),
            ("Delete", self.delete_selected),
            ("Report", self.show_detailed_report),
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
            "id", "type", "name", "resource_type", "date_added",
            "detail", "capacity_qty", "condition", "status"
        )

        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=13
        )

        headings = (
            "ID", "Type", "Resource Name", "Resource Type", "Date Added",
            "Location / Serial", "Capacity / Qty",
            "Condition", "Status"
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
        self.filter_resource_type_var.set("All")
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
        resource_type_var = tk.StringVar(value=self.filter_resource_type_var.get())
        condition_var = tk.StringVar(value=self.filter_condition_var.get())
        status_var = tk.StringVar(value=self.filter_status_var.get())

        ttk.Label(
            window,
            text="Filter Records",
            font=("Arial", 13, "bold")
        ).grid(row=0, column=0, columnspan=2, padx=15, pady=(15, 10))

        labels = (
            "Filter Type",
            "Resource Type",
            "Condition",
            "Status"
        )

        for row, text in enumerate(labels, start=1):
            ttk.Label(window, text=text + ":").grid(
                row=row, column=0, padx=15, pady=6, sticky="w"
            )

        type_combo = ttk.Combobox(
            window,
            textvariable=type_var,
            values=("All", "Facility", "Equipment"),
            state="readonly",
            width=24
        )
        type_combo.grid(row=1, column=1, padx=15, pady=6)

        # Only offer resource types that currently exist among the
        # records, computed fresh each time so deleted records don't
        # leave stale options in the list.
        used_types = sorted({
            record.resource_type for record in self.manager.get_all()
        })
        if resource_type_var.get() not in used_types:
            resource_type_var.set("All")

        resource_type_combo = ttk.Combobox(
            window,
            textvariable=resource_type_var,
            values=("All",) + tuple(used_types),
            state="readonly",
            width=24
        )
        resource_type_combo.grid(row=2, column=1, padx=15, pady=6)

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
            values=("All",) + STATUSES,
            state="readonly",
            width=24
        )
        status_combo.grid(row=4, column=1, padx=15, pady=6)

        def apply_and_close():
            self.filter_type_var.set(type_var.get())
            self.filter_resource_type_var.set(resource_type_var.get())
            self.filter_condition_var.set(condition_var.get())
            self.filter_status_var.set(status_var.get())
            self.apply_filter()
            window.destroy()

        def clear_and_close():
            self.clear_filter_values()
            self.apply_filter()
            window.destroy()

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

        resource_type = self.filter_resource_type_var.get()
        condition = self.filter_condition_var.get()
        status = self.filter_status_var.get()

        if resource_type != "All":
            records = [
                record for record in records
                if record.resource_type == resource_type
            ]

        if condition != "All":
            records = [
                record for record in records
                if record.condition == condition
            ]

        if status != "All":
            records = [
                record for record in records
                if record.status == status
            ]

        active_filters = []
        for name, value in (
            ("Type", self.filter_type_var.get()),
            ("Resource Type", resource_type),
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
            if isinstance(record, Facility):
                detail = record.location
                capacity_qty = record.capacity
            else:
                detail = record.serial_number or "-"
                capacity_qty = record.quantity

            self.tree.insert(
                "",
                "end",
                iid=str(record.record_id),
                values=(
                    record.code(),
                    record.record_type(),
                    record.resource_name,
                    record.resource_type,
                    record.date_added,
                    detail,
                    capacity_qty,
                    record.condition,
                    record.status
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
            elif column == "capacity_qty":
                number_match = re.match(r"^(\d+)", value)
                if number_match:
                    sort_value = (0, int(number_match.group(1)))
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

        if isinstance(record, Facility):
            text = (
                f"{record.code()} | {record.resource_name} | "
                f"{record.resource_type} | Added: {record.date_added} | "
                f"Location: {record.location} | "
                f"Capacity: {record.capacity} | "
                f"Condition: {record.condition} | "
                f"Status: {record.status} | "
                f"Remarks: {record.remarks or '-'}"
            )
        else:
            text = (
                f"{record.code()} | {record.resource_name} | "
                f"{record.resource_type} | Added: {record.date_added} | "
                f"Serial: {record.serial_number or '-'} | "
                f"Quantity: {record.quantity} | "
                f"Condition: {record.condition} | "
                f"Status: {record.status} | "
                f"Remarks: {record.remarks or '-'}"
            )

        self.detail_var.set(text)

    # ------------------------------------------------------------
    # Add Forms
    # ------------------------------------------------------------
    def add_facility_form(self):
        self.create_form(
            "Add Facility",
            [
                ("Facility Name", None),
                ("Facility Type", FACILITY_TYPES),
                ("Date Added (YYYY-MM-DD)", None),
                ("Location", None),
                ("Capacity", None),
                ("Condition", CONDITIONS),
                ("Status", STATUSES),
                ("Remarks", None)
            ],
            self.manager.add_facility
        )

    def add_equipment_form(self):
        self.create_form(
            "Add Equipment",
            [
                ("Equipment Name", None),
                ("Equipment Type", EQUIPMENT_TYPES),
                ("Date Added (YYYY-MM-DD)", None),
                ("Serial Number", None),
                ("Quantity", None),
                ("Condition", CONDITIONS),
                ("Status", STATUSES),
                ("Remarks", None)
            ],
            self.manager.add_equipment
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

                widgets[self.field_index_for_error(str(error))].focus_set()

                wrong_index = self.field_index_for_error(str(error))
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

    def field_index_for_error(self, error_message):
        """Map a validation error message to its form field position.

        Both the Facility and Equipment forms share the same layout:
        0 Name, 1 Resource Type, 2 Date Added, 3 Location/Serial,
        4 Capacity/Quantity, 5 Condition, 6 Status, 7 Remarks.
        """
        error_message = error_message.lower()

        if "resource name" in error_message:
            return 0
        elif "facility type" in error_message or "equipment type" in error_message:
            return 1
        elif "date added" in error_message:
            return 2
        elif "location" in error_message:
            return 3
        elif "capacity" in error_message or "quantity" in error_message:
            return 4
        elif "condition" in error_message:
            return 5
        elif "status" in error_message:
            return 6
        else:
            return 0

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

        if isinstance(record, Facility):
            fields = [
                ("Facility Name", None, record.resource_name),
                ("Facility Type", FACILITY_TYPES, record.resource_type),
                ("Date Added (YYYY-MM-DD)", None, record.date_added),
                ("Location", None, record.location),
                ("Capacity", None, str(record.capacity)),
                ("Condition", CONDITIONS, record.condition),
                ("Status", STATUSES, record.status),
                ("Remarks", None, record.remarks)
            ]
        else:
            fields = [
                ("Equipment Name", None, record.resource_name),
                ("Equipment Type", EQUIPMENT_TYPES, record.resource_type),
                ("Date Added (YYYY-MM-DD)", None, record.date_added),
                ("Serial Number", None, record.serial_number),
                ("Quantity", None, str(record.quantity)),
                ("Condition", CONDITIONS, record.condition),
                ("Status", STATUSES, record.status),
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

                wrong_index = self.field_index_for_error(str(error))
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
        """Display complete facility and equipment inventory statistics."""
        report = self.manager.detailed_report()
        condition_counts = self.manager.condition_summary()
        status_counts = self.manager.status_summary()

        lines = [
            "FACILITY & RESOURCE MANAGEMENT REPORT",
            "=" * 54,
            "",
            f"Total Records: {report['total_records']}",
            f"Total Facilities: {report['facility_count']}",
            f"Total Equipment Items: {report['equipment_count']}",
            f"Total Facility Capacity: {report['total_capacity']}",
            f"Total Equipment Quantity: {report['total_quantity']}",
            "",
            "RESOURCE TYPE SUMMARY",
            "-" * 54
        ]

        for resource_type, count in report["resource_types"].items():
            lines.append(f"{resource_type}: {count}")

        lines.extend([
            "",
            "STATUS SUMMARY",
            "-" * 54
        ])

        for status, count in status_counts.items():
            lines.append(f"{status}: {count}")

        lines.extend([
            "",
            "CONDITION SUMMARY",
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

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv")],
            initialfile="resource_records.csv"
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

    page = FacilityResourceManagementFrame(root)
    page.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()