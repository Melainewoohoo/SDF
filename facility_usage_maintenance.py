"""
BMCS1033 Software Development Fundamentals - Assignment
Application  : J. University Facilities Booking App
Module       : Facility Usage & Maintenance Management
Author       : <put your name here>

Purpose:
    Maintain facility usage logs and maintenance condition records as
    facilities are used and serviced over time. Supports the full record
    lifecycle: Create, Read (view/search), Update, and Delete (CRUD) for
    two related record types:
        - Usage Log        : who used a facility, when, and for how long
        - Maintenance Record: condition / servicing history of a facility

Rubric coverage in this single file:
    Selection, Loop, String Processing, File Processing, List,
    Set/Tuple/Dict, Predefined + user-defined Functions, Encapsulation,
    Inheritance, GUI (tkinter), Exception Handling, Comments.

Integration note for group members:
    This file can run standalone (python facility_usage_maintenance.py),
    or the FacilityUsageMaintenanceFrame class can be imported and
    embedded as a tab/page inside the group's shared main-menu window:
        from facility_usage_maintenance import FacilityUsageMaintenanceFrame
        frame = FacilityUsageMaintenanceFrame(parent_container)
        frame.pack(fill="both", expand=True)
"""

import json          # predefined module - file processing (persistence)
import os             # predefined module - checking file existence
import re              # predefined module - string validation (date format)
from datetime import datetime          # predefined module - timestamps
import tkinter as tk
from tkinter import ttk, messagebox

# ----------------------------------------------------------------------
# Constants (tuple/set demonstrate fixed, non-duplicated collections)
# ----------------------------------------------------------------------
DATA_FILE = "facility_records.json"

# Tuple: fixed, ordered set of allowed condition statuses (immutable)
CONDITION_STATUSES = ("Good", "Fair", "Poor", "Under Repair")

# Set: facility types seen so far must be unique -> a set fits naturally
FACILITY_TYPES = {"Classroom", "Lecture Hall", "Lab", "Gym",
                   "Court", "Pool", "Field", "Equipment"}

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")   # YYYY-MM-DD


# ----------------------------------------------------------------------
# Custom exception - used with exception handling for invalid input
# ----------------------------------------------------------------------
class InvalidRecordError(Exception):
    """Raised when a facility record fails validation."""
    pass


# ----------------------------------------------------------------------
# Base class (Inheritance root) - Encapsulation via "protected" attrs
# and property getters/setters
# ----------------------------------------------------------------------
class FacilityRecord:
    """Common fields shared by every kind of facility record."""

    _next_id = 1  # class-level counter shared by all subclasses

    def __init__(self, facility_name, facility_type, date_str, remarks=""):
        self._record_id = FacilityRecord._next_id
        FacilityRecord._next_id += 1

        self.facility_name = facility_name      # goes through setter (validation)
        self.facility_type = facility_type
        self.date = date_str
        self._remarks = remarks.strip()

        FACILITY_TYPES.add(self.facility_type)  # keep the set up to date

    # ---- Encapsulated properties -------------------------------------
    @property
    def record_id(self):
        return self._record_id

    @property
    def facility_name(self):
        return self._facility_name

    @facility_name.setter
    def facility_name(self, value):
        value = value.strip()                    # string processing
        if not value:
            raise InvalidRecordError("Facility name cannot be empty.")
        self._facility_name = value.title()       # string processing

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        value = value.strip()
        if not DATE_PATTERN.match(value):          # string processing (regex)
            raise InvalidRecordError(
                f"Date '{value}' must be in YYYY-MM-DD format.")
        self._date = value

    @property
    def remarks(self):
        return self._remarks

    @remarks.setter
    def remarks(self, value):
        self._remarks = value.strip()

    # ---- Shared behaviour ----------------------------------------------
    def record_type(self):
        """Overridden by subclasses; base kept generic."""
        return "Facility Record"

    def to_dict(self):
        """Convert record to a plain dict (for JSON file processing)."""
        return {
            "type": self.record_type(),
            "record_id": self._record_id,
            "facility_name": self._facility_name,
            "facility_type": self.facility_type,
            "date": self._date,
            "remarks": self._remarks,
        }

    def summary_line(self):
        return (f"[{self._record_id:04d}] {self.record_type():<12} | "
                f"{self._facility_name:<15} | {self._date}")

    def __str__(self):
        return self.summary_line()


# ----------------------------------------------------------------------
# Subclass 1 - Usage Log (Inheritance)
# ----------------------------------------------------------------------
class UsageLog(FacilityRecord):
    """A single facility usage event."""

    def __init__(self, facility_name, facility_type, date_str,
                 user_name, purpose, duration_hours, remarks=""):
        super().__init__(facility_name, facility_type, date_str, remarks)
        self.user_name = user_name
        self.purpose = purpose.strip()
        self.duration_hours = duration_hours   # validated via setter

    @property
    def user_name(self):
        return self._user_name

    @user_name.setter
    def user_name(self, value):
        value = value.strip()
        if not value:
            raise InvalidRecordError("User name cannot be empty.")
        self._user_name = value.title()

    @property
    def duration_hours(self):
        return self._duration_hours

    @duration_hours.setter
    def duration_hours(self, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise InvalidRecordError("Duration must be a number (hours).")
        if value <= 0 or value > 24:              # selection (if-else)
            raise InvalidRecordError("Duration must be between 0 and 24 hours.")
        self._duration_hours = value

    def record_type(self):
        return "Usage Log"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "user_name": self._user_name,
            "purpose": self.purpose,
            "duration_hours": self._duration_hours,
        })
        return data

    def summary_line(self):
        base = super().summary_line()
        return f"{base} | {self._user_name} ({self._duration_hours}h) - {self.purpose}"


# ----------------------------------------------------------------------
# Subclass 2 - Maintenance Record (Inheritance)
# ----------------------------------------------------------------------
class MaintenanceRecord(FacilityRecord):
    """Condition / servicing history of a facility."""

    def __init__(self, facility_name, facility_type, date_str,
                 condition_status, technician, next_service_date, remarks=""):
        super().__init__(facility_name, facility_type, date_str, remarks)
        self.condition_status = condition_status
        self.technician = technician.strip()
        self.next_service_date = next_service_date

    @property
    def condition_status(self):
        return self._condition_status

    @condition_status.setter
    def condition_status(self, value):
        value = value.strip().title()
        if value not in CONDITION_STATUSES:        # selection (if-else via `in`)
            raise InvalidRecordError(
                f"Condition must be one of {CONDITION_STATUSES}.")
        self._condition_status = value

    @property
    def next_service_date(self):
        return self._next_service_date

    @next_service_date.setter
    def next_service_date(self, value):
        value = value.strip()
        if value and not DATE_PATTERN.match(value):
            raise InvalidRecordError("Next service date must be YYYY-MM-DD.")
        self._next_service_date = value

    def record_type(self):
        return "Maintenance"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "condition_status": self._condition_status,
            "technician": self.technician,
            "next_service_date": self._next_service_date,
        })
        return data

    def summary_line(self):
        base = super().summary_line()
        return f"{base} | {self._condition_status} - tech: {self.technician}"


# ----------------------------------------------------------------------
# Manager class - owns the collection of records + file persistence
# (Encapsulation: the dict of records is "private")
# ----------------------------------------------------------------------
class FacilityManager:
    def __init__(self, file_path=DATA_FILE):
        self._file_path = file_path
        self._records = {}          # dict: record_id -> FacilityRecord
        self.load_from_file()

    # ---- CRUD: Create ---------------------------------------------------
    def add_usage_log(self, **kwargs):
        record = UsageLog(**kwargs)
        self._records[record.record_id] = record
        self.save_to_file()
        return record

    def add_maintenance_record(self, **kwargs):
        record = MaintenanceRecord(**kwargs)
        self._records[record.record_id] = record
        self.save_to_file()
        return record

    # ---- CRUD: Read -------------------------------------------------------
    def get_all(self):
        # list: ordered collection returned for the GUI to iterate over
        return list(self._records.values())

    def search(self, keyword):
        """String-processing search across facility name / remarks / user."""
        keyword = keyword.strip().lower()
        results = []
        for record in self._records.values():      # loop
            haystack = " ".join([
                record.facility_name.lower(),
                record.remarks.lower(),
                getattr(record, "user_name", "").lower(),
                getattr(record, "technician", "").lower(),
            ])
            if keyword in haystack:                  # string processing
                results.append(record)
        return results

    # ---- CRUD: Update -----------------------------------------------------
    def update_remarks(self, record_id, new_remarks):
        record = self._records.get(record_id)
        if record is None:
            raise InvalidRecordError(f"Record {record_id} not found.")
        record.remarks = new_remarks
        self.save_to_file()

    def update_condition(self, record_id, new_status):
        record = self._records.get(record_id)
        if record is None or not isinstance(record, MaintenanceRecord):
            raise InvalidRecordError("Not a maintenance record.")
        record.condition_status = new_status
        self.save_to_file()

    # ---- CRUD: Delete -------------------------------------------------------
    def delete(self, record_id):
        if record_id in self._records:
            del self._records[record_id]
            self.save_to_file()
        else:
            raise InvalidRecordError(f"Record {record_id} not found.")

    # ---- File processing ------------------------------------------------
    def save_to_file(self):
        try:
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump([r.to_dict() for r in self._records.values()], f, indent=2)
        except OSError as e:
            raise InvalidRecordError(f"Could not save data: {e}")

    def load_from_file(self):
        if not os.path.exists(self._file_path):
            return
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
        except (OSError, json.JSONDecodeError):
            raw_list = []

        max_id = 0
        for raw in raw_list:                          # loop rebuilding objects
            try:
                if raw["type"] == "Usage Log":
                    record = UsageLog(
                        raw["facility_name"], raw["facility_type"], raw["date"],
                        raw["user_name"], raw["purpose"], raw["duration_hours"],
                        raw.get("remarks", ""))
                else:
                    record = MaintenanceRecord(
                        raw["facility_name"], raw["facility_type"], raw["date"],
                        raw["condition_status"], raw["technician"],
                        raw.get("next_service_date", ""), raw.get("remarks", ""))
                record._record_id = raw["record_id"]   # restore original id
                self._records[record.record_id] = record
                max_id = max(max_id, record.record_id)
            except (KeyError, InvalidRecordError):
                continue   # skip corrupt rows instead of crashing
        FacilityRecord._next_id = max_id + 1

    # ---- Simple report using set/dict for aggregation --------------------
    def condition_summary(self):
        """Counts maintenance records per condition status -> dict."""
        counts = {status: 0 for status in CONDITION_STATUSES}
        for record in self._records.values():
            if isinstance(record, MaintenanceRecord):
                counts[record.condition_status] += 1
        return counts


# ----------------------------------------------------------------------
# GUI (tkinter) - consistent, user-friendly layout
# ----------------------------------------------------------------------
class FacilityUsageMaintenanceFrame(ttk.Frame):
    """Embeddable GUI page for this module."""

    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.manager = FacilityManager()
        self._build_widgets()
        self._refresh_table()

    # ---- widget construction --------------------------------------------
    def _build_widgets(self):
        ttk.Label(self, text="Facility Usage & Maintenance Management",
                  font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=4, pady=(0, 10), sticky="w")

        # --- search bar ---
        ttk.Label(self, text="Search:").grid(row=1, column=0, sticky="w")
        self.search_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.search_var, width=30).grid(
            row=1, column=1, sticky="w")
        ttk.Button(self, text="Search", command=self._on_search).grid(
            row=1, column=2, sticky="w")
        ttk.Button(self, text="Show All", command=self._refresh_table).grid(
            row=1, column=3, sticky="w")

        # --- table of records ---
        columns = ("id", "type", "facility", "date", "detail")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        for col, width in zip(columns, (50, 90, 140, 90, 260)):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=width)
        self.tree.grid(row=2, column=0, columnspan=4, pady=10, sticky="nsew")

        # --- action buttons ---
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=4, sticky="w")
        ttk.Button(btn_frame, text="Add Usage Log",
                   command=self._open_usage_form).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Add Maintenance Record",
                   command=self._open_maintenance_form).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Edit Remarks",
                   command=self._edit_remarks).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Delete",
                   command=self._delete_selected).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Condition Summary",
                   command=self._show_summary).pack(side="left", padx=3)

    # ---- table helpers ------------------------------------------------
    def _refresh_table(self, records=None):
        self.tree.delete(*self.tree.get_children())
        records = records if records is not None else self.manager.get_all()
        for r in records:                              # loop
            if isinstance(r, UsageLog):
                detail = f"{r.user_name}, {r.duration_hours}h - {r.purpose}"
            else:
                detail = f"{r.condition_status}, tech: {r.technician}"
            self.tree.insert("", "end", iid=str(r.record_id),
                              values=(r.record_id, r.record_type(),
                                      r.facility_name, r.date, detail))

    def _selected_id(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No selection", "Please select a record first.")
            return None
        return int(selection[0])

    def _on_search(self):
        results = self.manager.search(self.search_var.get())
        self._refresh_table(results)

    # ---- add forms -----------------------------------------------------
    def _open_usage_form(self):
        self._record_form(
            title="Add Usage Log",
            fields=["Facility name", "Facility type", "Date (YYYY-MM-DD)",
                    "User name", "Purpose", "Duration (hours)"],
            on_submit=self._submit_usage_log)

    def _open_maintenance_form(self):
        self._record_form(
            title="Add Maintenance Record",
            fields=["Facility name", "Facility type", "Date (YYYY-MM-DD)",
                    f"Condition {CONDITION_STATUSES}", "Technician",
                    "Next service date (YYYY-MM-DD, optional)"],
            on_submit=self._submit_maintenance_record)

    def _record_form(self, title, fields, on_submit):
        win = tk.Toplevel(self)
        win.title(title)
        entries = []
        for i, label in enumerate(fields):
            ttk.Label(win, text=label).grid(row=i, column=0, padx=5, pady=4, sticky="w")
            var = tk.StringVar()
            ttk.Entry(win, textvariable=var, width=30).grid(row=i, column=1, padx=5, pady=4)
            entries.append(var)

        def submit():
            values = [e.get() for e in entries]
            try:
                on_submit(values)
                win.destroy()
                self._refresh_table()
            except InvalidRecordError as err:          # exception handling
                messagebox.showerror("Invalid input", str(err))

        ttk.Button(win, text="Save", command=submit).grid(
            row=len(fields), column=0, columnspan=2, pady=8)

    def _submit_usage_log(self, values):
        facility_name, facility_type, date_str, user_name, purpose, duration = values
        self.manager.add_usage_log(
            facility_name=facility_name, facility_type=facility_type,
            date_str=date_str, user_name=user_name,
            purpose=purpose, duration_hours=duration)

    def _submit_maintenance_record(self, values):
        (facility_name, facility_type, date_str, condition,
         technician, next_service) = values
        self.manager.add_maintenance_record(
            facility_name=facility_name, facility_type=facility_type,
            date_str=date_str, condition_status=condition,
            technician=technician, next_service_date=next_service)

    # ---- edit / delete ---------------------------------------------------
    def _edit_remarks(self):
        record_id = self._selected_id()
        if record_id is None:
            return
        new_text = tk.simpledialog.askstring(
            "Edit remarks", "New remarks:") if hasattr(tk, "simpledialog") else None
        if new_text is None:
            return
        try:
            self.manager.update_remarks(record_id, new_text)
            self._refresh_table()
        except InvalidRecordError as err:
            messagebox.showerror("Error", str(err))

    def _delete_selected(self):
        record_id = self._selected_id()
        if record_id is None:
            return
        if messagebox.askyesno("Confirm", f"Delete record {record_id}?"):
            try:
                self.manager.delete(record_id)
                self._refresh_table()
            except InvalidRecordError as err:
                messagebox.showerror("Error", str(err))

    def _show_summary(self):
        summary = self.manager.condition_summary()
        lines = [f"{status}: {count}" for status, count in summary.items()]
        messagebox.showinfo("Condition Summary", "\n".join(lines))


# ----------------------------------------------------------------------
# Standalone runner
# ----------------------------------------------------------------------
def main():
    import tkinter.simpledialog  # noqa: F401  (enables tk.simpledialog above)
    root = tk.Tk()
    root.title("University Facilities Booking App - Facility Usage & Maintenance")
    root.geometry("820x480")
    frame = FacilityUsageMaintenanceFrame(root)
    frame.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
