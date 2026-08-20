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

GUI note:
    Tkinter cannot reproduce a web-style layout pixel-for-pixel (no real
    box-shadows / rounded corners), but this version approximates the
    reference design: a header bar with coloured action buttons, a
    filter/search row, a striped table with coloured condition/status
    badges, and a details + maintenance + colour-guide panel underneath.
"""

import json          # predefined module - file processing (persistence)
import os             # predefined module - checking file existence
import re              # predefined module - string validation (date format)
import csv             # predefined module - export to CSV
from datetime import datetime          # predefined module - timestamps
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

# ----------------------------------------------------------------------
# Constants (tuple/set demonstrate fixed, non-duplicated collections)
# ----------------------------------------------------------------------
DATA_FILE = "facility_records.json"

# Tuple: fixed, ordered set of allowed condition statuses (immutable)
CONDITION_STATUSES = ("Good", "Fair", "Poor", "Under Repair")

# Tuple: fixed, ordered set of allowed maintenance statuses (immutable)
MAINTENANCE_STATUSES = ("Not Required", "Scheduled", "Completed", "Overdue")

# Set: facility types seen so far must be unique -> a set fits naturally
FACILITY_TYPES = {"Classroom", "Lecture Hall", "Lab", "Gym",
                   "Court", "Pool", "Field", "Equipment"}

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")   # YYYY-MM-DD

# ----------------------------------------------------------------------
# Colour palette (dict) - keeps every widget's colours consistent and
# is the single place to retheme the whole screen.
# ----------------------------------------------------------------------
PALETTE = {
    "bg":            "#F3F5FA",
    "card":          "#FFFFFF",
    "border":        "#E4E8F1",
    "text":          "#1F2430",
    "muted":         "#6B7280",
    "primary":       "#4A5CF6",
    "primary_text":  "#FFFFFF",
    "green":         "#16A34A",
    "green_bg":      "#DCFCE7",
    "yellow":        "#B45309",
    "yellow_bg":     "#FEF3C7",
    "red":           "#DC2626",
    "red_bg":        "#FEE2E2",
    "gray":          "#4B5563",
    "gray_bg":       "#E5E7EB",
    "row_alt":       "#F7F9FC",
    "select":        "#E8ECFE",
}

# Maps status text -> (fg colour, bg colour) badge colours
CONDITION_COLORS = {
    "Good":          ("green", "green_bg"),
    "Fair":          ("yellow", "yellow_bg"),
    "Poor":          ("red", "red_bg"),
    "Under Repair":  ("red", "red_bg"),
}
MAINTENANCE_COLORS = {
    "Not Required":  ("gray", "gray_bg"),
    "Scheduled":     ("yellow", "yellow_bg"),
    "Completed":     ("green", "green_bg"),
    "Overdue":       ("red", "red_bg"),
}


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

    def code(self):
        """Short display code, e.g. USG0001 / MTN0001, for the table."""
        prefix = "USG" if self.record_type() == "Usage Log" else "MTN"
        return f"{prefix}{self._record_id:04d}"

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
                 condition_status, technician, next_service_date,
                 maintenance_status="Not Required", remarks=""):
        super().__init__(facility_name, facility_type, date_str, remarks)
        self.condition_status = condition_status
        self.technician = technician.strip()
        self.next_service_date = next_service_date
        self.maintenance_status = maintenance_status

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
    def maintenance_status(self):
        return self._maintenance_status

    @maintenance_status.setter
    def maintenance_status(self, value):
        value = value.strip().title()
        if value not in MAINTENANCE_STATUSES:
            raise InvalidRecordError(
                f"Maintenance status must be one of {MAINTENANCE_STATUSES}.")
        self._maintenance_status = value

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
            "maintenance_status": self._maintenance_status,
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

    def get(self, record_id):
        return self._records.get(record_id)

    def search(self, keyword):
        """String-processing search across facility name / remarks / user."""
        keyword = keyword.strip().lower()
        if not keyword:
            return self.get_all()
        results = []
        for record in self._records.values():      # loop
            haystack = " ".join([
                record.facility_name.lower(),
                record.remarks.lower(),
                record.code().lower(),
                getattr(record, "user_name", "").lower(),
                getattr(record, "technician", "").lower(),
            ])
            if keyword in haystack:                  # string processing
                results.append(record)
        return results

    def filter_by_condition(self, records, status):
        if status == "All Status":
            return records
        return [r for r in records
                if isinstance(r, MaintenanceRecord) and r.condition_status == status]

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

    def update_maintenance_status(self, record_id, new_status):
        record = self._records.get(record_id)
        if record is None or not isinstance(record, MaintenanceRecord):
            raise InvalidRecordError("Not a maintenance record.")
        record.maintenance_status = new_status
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
                        raw.get("next_service_date", ""),
                        raw.get("maintenance_status", "Not Required"),
                        raw.get("remarks", ""))
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

    def export_csv(self, path):
        """Export every record to a flat CSV file (file processing)."""
        fieldnames = ["code", "type", "facility_name", "facility_type", "date",
                      "user_or_tech", "detail", "condition_status",
                      "maintenance_status", "remarks"]
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in self._records.values():
                    if isinstance(r, UsageLog):
                        row = {"user_or_tech": r.user_name,
                               "detail": f"{r.duration_hours}h - {r.purpose}",
                               "condition_status": "", "maintenance_status": ""}
                    else:
                        row = {"user_or_tech": r.technician,
                               "detail": f"Next service: {r.next_service_date}",
                               "condition_status": r.condition_status,
                               "maintenance_status": r.maintenance_status}
                    row.update({"code": r.code(), "type": r.record_type(),
                                "facility_name": r.facility_name,
                                "facility_type": r.facility_type,
                                "date": r.date, "remarks": r.remarks})
                    writer.writerow(row)
        except OSError as e:
            raise InvalidRecordError(f"Could not export data: {e}")


# ----------------------------------------------------------------------
# Small reusable widget: a coloured "badge" label, like the status pills
# in the reference design.
# ----------------------------------------------------------------------
def make_badge(parent, text, color_key):
    fg_key, bg_key = CONDITION_COLORS.get(text) or MAINTENANCE_COLORS.get(text) \
        or ("gray", "gray_bg")
    lbl = tk.Label(parent, text=text, font=("Segoe UI", 9, "bold"),
                   fg=PALETTE[fg_key], bg=PALETTE[bg_key],
                   padx=10, pady=2)
    return lbl


# ----------------------------------------------------------------------
# GUI (tkinter) - card-style layout inspired by the reference design
# ----------------------------------------------------------------------
class FacilityUsageMaintenanceFrame(ttk.Frame):
    """Embeddable GUI page for this module."""

    def __init__(self, parent):
        super().__init__(parent, padding=0)
        self.configure(style="Bg.TFrame")
        self.manager = FacilityManager()
        self.selected_record = None
        self._setup_styles()
        self._build_widgets()
        self._refresh_table()

    # ---- theming -----------------------------------------------------
    def _setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Bg.TFrame", background=PALETTE["bg"])
        style.configure("Card.TFrame", background=PALETTE["card"])
        style.configure("Card.TLabel", background=PALETTE["card"],
                         foreground=PALETTE["text"])
        style.configure("Title.TLabel", background=PALETTE["bg"],
                         foreground=PALETTE["text"],
                         font=("Segoe UI", 16, "bold"))
        style.configure("Subtitle.TLabel", background=PALETTE["bg"],
                         foreground=PALETTE["muted"], font=("Segoe UI", 9))
        style.configure("CardTitle.TLabel", background=PALETTE["card"],
                         foreground=PALETTE["text"], font=("Segoe UI", 11, "bold"))
        style.configure("FieldLabel.TLabel", background=PALETTE["card"],
                         foreground=PALETTE["muted"], font=("Segoe UI", 9))

        style.configure("Treeview", background=PALETTE["card"],
                         fieldbackground=PALETTE["card"],
                         foreground=PALETTE["text"], rowheight=30,
                         borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=PALETTE["row_alt"],
                         foreground=PALETTE["muted"], font=("Segoe UI", 9, "bold"),
                         relief="flat")
        style.map("Treeview", background=[("selected", PALETTE["select"])],
                  foreground=[("selected", PALETTE["text"])])

    def _styled_button(self, parent, text, command, kind="outline"):
        """tk.Button (not ttk) so we get full colour control, like the
        blue / green-outline / red-outline buttons in the reference."""
        if kind == "solid":
            return tk.Button(parent, text=text, command=command,
                              bg=PALETTE["primary"], fg=PALETTE["primary_text"],
                              activebackground=PALETTE["primary"],
                              activeforeground=PALETTE["primary_text"],
                              font=("Segoe UI", 9, "bold"), relief="flat",
                              padx=12, pady=6, cursor="hand2", bd=0)
        colors = {"green": PALETTE["green"], "red": PALETTE["red"],
                  "gray": PALETTE["muted"]}
        color = colors.get(kind, PALETTE["muted"])
        return tk.Button(parent, text=text, command=command,
                          bg=PALETTE["card"], fg=color,
                          activebackground=PALETTE["row_alt"], activeforeground=color,
                          font=("Segoe UI", 9, "bold"), relief="solid",
                          highlightbackground=color, bd=1,
                          padx=12, pady=5, cursor="hand2")

    # ---- widget construction --------------------------------------------
    def _build_widgets(self):
        self.grid_columnconfigure(0, weight=1)

        outer = ttk.Frame(self, style="Bg.TFrame", padding=20)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------------- Header ----------------
        header = ttk.Frame(outer, style="Bg.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.grid_columnconfigure(0, weight=1)

        title_box = ttk.Frame(header, style="Bg.TFrame")
        title_box.grid(row=0, column=0, sticky="w")
        ttk.Label(title_box, text="Facility Usage & Maintenance Management",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_box, text="Maintain facility usage logs and maintenance condition records.",
                  style="Subtitle.TLabel").pack(anchor="w")

        btn_box = ttk.Frame(header, style="Bg.TFrame")
        btn_box.grid(row=0, column=1, sticky="e")
        self._styled_button(btn_box, "+ Add Usage Log", self._open_usage_form,
                             kind="solid").pack(side="left", padx=(0, 6))
        self._styled_button(btn_box, "+ Add Maintenance", self._open_maintenance_form,
                             kind="solid").pack(side="left", padx=(0, 6))
        self._styled_button(btn_box, "Refresh", self._refresh_table,
                             kind="green").pack(side="left", padx=(0, 6))
        self._styled_button(btn_box, "Export", self._export_csv,
                             kind="red").pack(side="left")

        # ---------------- Search / filter card ----------------
        search_card = tk.Frame(outer, bg=PALETTE["card"],
                                highlightbackground=PALETTE["border"],
                                highlightthickness=1)
        search_card.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        for i in range(4):
            search_card.grid_columnconfigure(i, weight=0)
        search_card.grid_columnconfigure(1, weight=1)

        tk.Label(search_card, text="Search:", bg=PALETTE["card"],
                 fg=PALETTE["muted"], font=("Segoe UI", 9)).grid(
            row=0, column=0, padx=(12, 4), pady=10)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_card, textvariable=self.search_var,
                                 relief="solid", bd=1, font=("Segoe UI", 9))
        search_entry.grid(row=0, column=1, sticky="ew", padx=4, pady=10)
        search_entry.bind("<Return>", lambda e: self._apply_filters())

        self.status_filter_var = tk.StringVar(value="All Status")
        status_combo = ttk.Combobox(search_card, textvariable=self.status_filter_var,
                                     state="readonly", width=14,
                                     values=("All Status",) + CONDITION_STATUSES)
        status_combo.grid(row=0, column=2, padx=4, pady=10)
        status_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        self._styled_button(search_card, "Search", self._apply_filters,
                             kind="solid").grid(row=0, column=3, padx=(4, 12), pady=10)

        # ---------------- Table card ----------------
        table_card = tk.Frame(outer, bg=PALETTE["card"],
                               highlightbackground=PALETTE["border"],
                               highlightthickness=1)
        table_card.grid(row=2, column=0, sticky="ew", pady=(0, 14))
        table_card.grid_columnconfigure(0, weight=1)

        tk.Label(table_card, text="Usage & Maintenance Records", bg=PALETTE["card"],
                 fg=PALETTE["text"], font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 6))

        columns = ("code", "facility", "date", "who", "detail", "condition", "status")
        headings = ("Usage ID", "Facility", "Date", "Used By", "Purpose / Detail",
                    "Condition", "Maintenance Status")
        widths = (85, 150, 90, 130, 200, 100, 140)

        tree_frame = ttk.Frame(table_card, style="Card.TFrame")
        tree_frame.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                  height=8)
        for col, head, w in zip(columns, headings, widths):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=w, anchor="w")
        self.tree.grid(row=0, column=0, sticky="ew")
        self.tree.tag_configure("odd", background=PALETTE["row_alt"])
        self.tree.tag_configure("even", background=PALETTE["card"])
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        action_row = ttk.Frame(table_card, style="Card.TFrame")
        action_row.grid(row=2, column=0, sticky="w", padx=14, pady=(0, 12))
        self._styled_button(action_row, "Delete Selected", self._delete_selected,
                             kind="red").pack(side="left")

        # ---------------- Bottom: details / maintenance / guide ----------------
        bottom = ttk.Frame(outer, style="Bg.TFrame")
        bottom.grid(row=3, column=0, sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        bottom.grid_columnconfigure(2, weight=1)

        self._build_details_card(bottom, col=0)
        self._build_maintenance_card(bottom, col=1)
        self._build_guide_card(bottom, col=2)

    # ---- Record details card -------------------------------------------
    def _build_details_card(self, parent, col):
        card = tk.Frame(parent, bg=PALETTE["card"],
                         highlightbackground=PALETTE["border"], highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew", padx=(0, 10))
        card.grid_columnconfigure(1, weight=1)

        tk.Label(card, text="Record Details", bg=PALETTE["card"], fg=PALETTE["text"],
                  font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 8))

        labels = ["Usage ID", "Facility Name", "Facility Type", "Date",
                  "Used By / Technician", "Detail", "Remarks"]
        self.detail_vars = {}
        for i, label in enumerate(labels, start=1):
            tk.Label(card, text=label, bg=PALETTE["card"], fg=PALETTE["muted"],
                      font=("Segoe UI", 9)).grid(row=i, column=0, sticky="w",
                                                  padx=14, pady=4)
            var = tk.StringVar(value="-")
            tk.Label(card, textvariable=var, bg=PALETTE["card"], fg=PALETTE["text"],
                      font=("Segoe UI", 9, "bold"), anchor="w", wraplength=180).grid(
                row=i, column=1, sticky="w", padx=(0, 14), pady=4)
            self.detail_vars[label] = var

        btn_row = ttk.Frame(card, style="Card.TFrame")
        btn_row.grid(row=len(labels) + 1, column=0, columnspan=2, sticky="w",
                     padx=14, pady=(10, 14))
        self._styled_button(btn_row, "Edit Remarks", self._edit_remarks,
                             kind="green").pack(side="left", padx=(0, 6))
        self._styled_button(btn_row, "Clear", lambda: self._select_row(None),
                             kind="gray").pack(side="left")

    # ---- Maintenance information card ------------------------------------
    def _build_maintenance_card(self, parent, col):
        card = tk.Frame(parent, bg=PALETTE["card"],
                         highlightbackground=PALETTE["border"], highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew", padx=(0, 10))
        card.grid_columnconfigure(1, weight=1)

        tk.Label(card, text="Maintenance Information", bg=PALETTE["card"],
                  fg=PALETTE["text"], font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 8))

        tk.Label(card, text="Current Condition", bg=PALETTE["card"],
                  fg=PALETTE["muted"], font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky="w", padx=14, pady=6)
        self.condition_badge_holder = ttk.Frame(card, style="Card.TFrame")
        self.condition_badge_holder.grid(row=1, column=1, sticky="w", padx=(0, 14))

        tk.Label(card, text="Maintenance Status", bg=PALETTE["card"],
                  fg=PALETTE["muted"], font=("Segoe UI", 9)).grid(
            row=2, column=0, sticky="w", padx=14, pady=6)
        self.status_badge_holder = ttk.Frame(card, style="Card.TFrame")
        self.status_badge_holder.grid(row=2, column=1, sticky="w", padx=(0, 14))

        tk.Label(card, text="Next Service Date", bg=PALETTE["card"],
                  fg=PALETTE["muted"], font=("Segoe UI", 9)).grid(
            row=3, column=0, sticky="w", padx=14, pady=6)
        self.next_service_var = tk.StringVar(value="-")
        tk.Label(card, textvariable=self.next_service_var, bg=PALETTE["card"],
                  fg=PALETTE["text"], font=("Segoe UI", 9, "bold")).grid(
            row=3, column=1, sticky="w", padx=(0, 14), pady=6)

        btn_row = ttk.Frame(card, style="Card.TFrame")
        btn_row.grid(row=4, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 14))
        self._styled_button(btn_row, "Update Condition", self._update_condition,
                             kind="green").pack(side="left", padx=(0, 6))
        self._styled_button(btn_row, "Update Status", self._update_maintenance_status,
                             kind="green").pack(side="left")

    # ---- Colour guide card -------------------------------------------
    def _build_guide_card(self, parent, col):
        card = tk.Frame(parent, bg=PALETTE["card"],
                         highlightbackground=PALETTE["border"], highlightthickness=1)
        card.grid(row=0, column=col, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        tk.Label(card, text="Condition Guide", bg=PALETTE["card"], fg=PALETTE["text"],
                  font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", padx=14, pady=(12, 8))

        condition_notes = {
            "Good": "No issues. Facility in good condition.",
            "Fair": "Minor issues. Monitor regularly.",
            "Poor": "Major issues. Needs attention.",
            "Under Repair": "Currently being serviced.",
        }
        r = 1
        for status in CONDITION_STATUSES:
            row = ttk.Frame(card, style="Card.TFrame")
            row.grid(row=r, column=0, sticky="w", padx=14, pady=4)
            make_badge(row, status, status).pack(side="left")
            tk.Label(row, text="  " + condition_notes[status], bg=PALETTE["card"],
                      fg=PALETTE["muted"], font=("Segoe UI", 8)).pack(side="left")
            r += 1

        tk.Label(card, text="Maintenance Status Guide", bg=PALETTE["card"],
                  fg=PALETTE["text"], font=("Segoe UI", 11, "bold")).grid(
            row=r, column=0, sticky="w", padx=14, pady=(14, 8))
        r += 1

        status_notes = {
            "Not Required": "No maintenance needed.",
            "Scheduled": "Maintenance planned.",
            "Completed": "Maintenance completed.",
            "Overdue": "Maintenance is overdue.",
        }
        for status in MAINTENANCE_STATUSES:
            row = ttk.Frame(card, style="Card.TFrame")
            row.grid(row=r, column=0, sticky="w", padx=14, pady=4)
            make_badge(row, status, status).pack(side="left")
            tk.Label(row, text="  " + status_notes[status], bg=PALETTE["card"],
                      fg=PALETTE["muted"], font=("Segoe UI", 8)).pack(side="left")
            r += 1

        self._styled_button(card, "Condition Summary", self._show_summary,
                             kind="gray").grid(row=r, column=0, sticky="w",
                                                padx=14, pady=(10, 14))

    # ---- table helpers ------------------------------------------------
    def _refresh_table(self, records=None):
        self.search_var.set("")
        self.status_filter_var.set("All Status")
        self._populate(self.manager.get_all())

    def _apply_filters(self):
        records = self.manager.search(self.search_var.get())
        records = self.manager.filter_by_condition(records, self.status_filter_var.get())
        self._populate(records)

    def _populate(self, records):
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(records):                              # loop
            tag = "odd" if i % 2 else "even"
            if isinstance(r, UsageLog):
                who = r.user_name
                detail = f"{r.duration_hours}h - {r.purpose}"
                condition, status = "-", "-"
            else:
                who = r.technician
                detail = f"Next service: {r.next_service_date or '-'}"
                condition, status = r.condition_status, r.maintenance_status
            self.tree.insert("", "end", iid=str(r.record_id), tags=(tag,),
                              values=(r.code(), r.facility_name, r.date, who,
                                      detail, condition, status))

    def _selected_id(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No selection", "Please select a record first.")
            return None
        return int(selection[0])

    def _on_select(self, event=None):
        selection = self.tree.selection()
        self._select_row(int(selection[0]) if selection else None)

    def _select_row(self, record_id):
        if record_id is None:
            self.selected_record = None
            for var in self.detail_vars.values():
                var.set("-")
            self.next_service_var.set("-")
            for widget in list(self.condition_badge_holder.children.values()):
                widget.destroy()
            for widget in list(self.status_badge_holder.children.values()):
                widget.destroy()
            return

        record = self.manager.get(record_id)
        if record is None:
            return
        self.selected_record = record
        self.detail_vars["Usage ID"].set(record.code())
        self.detail_vars["Facility Name"].set(record.facility_name)
        self.detail_vars["Facility Type"].set(record.facility_type)
        self.detail_vars["Date"].set(record.date)
        self.detail_vars["Remarks"].set(record.remarks or "-")

        for widget in list(self.condition_badge_holder.children.values()):
            widget.destroy()
        for widget in list(self.status_badge_holder.children.values()):
            widget.destroy()

        if isinstance(record, UsageLog):
            self.detail_vars["Used By / Technician"].set(record.user_name)
            self.detail_vars["Detail"].set(f"{record.duration_hours}h - {record.purpose}")
            self.next_service_var.set("-")
            tk.Label(self.condition_badge_holder, text="N/A", bg=PALETTE["card"],
                      fg=PALETTE["muted"]).pack()
            tk.Label(self.status_badge_holder, text="N/A", bg=PALETTE["card"],
                      fg=PALETTE["muted"]).pack()
        else:
            self.detail_vars["Used By / Technician"].set(record.technician)
            self.detail_vars["Detail"].set(f"Condition check on {record.date}")
            self.next_service_var.set(record.next_service_date or "-")
            make_badge(self.condition_badge_holder, record.condition_status,
                       record.condition_status).pack()
            make_badge(self.status_badge_holder, record.maintenance_status,
                       record.maintenance_status).pack()

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
                    "Next service date (YYYY-MM-DD, optional)",
                    f"Maintenance status {MAINTENANCE_STATUSES}"],
            on_submit=self._submit_maintenance_record)

    def _record_form(self, title, fields, on_submit):
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=PALETTE["card"])
        entries = []
        for i, label in enumerate(fields):
            tk.Label(win, text=label, bg=PALETTE["card"], fg=PALETTE["muted"],
                      font=("Segoe UI", 9)).grid(row=i, column=0, padx=10, pady=6, sticky="w")
            var = tk.StringVar()
            tk.Entry(win, textvariable=var, width=32, relief="solid", bd=1).grid(
                row=i, column=1, padx=10, pady=6)
            entries.append(var)

        def submit():
            values = [e.get() for e in entries]
            try:
                on_submit(values)
                win.destroy()
                self._refresh_table()
            except InvalidRecordError as err:          # exception handling
                messagebox.showerror("Invalid input", str(err))

        self._styled_button(win, "Save", submit, kind="solid").grid(
            row=len(fields), column=0, columnspan=2, pady=12)

    def _submit_usage_log(self, values):
        facility_name, facility_type, date_str, user_name, purpose, duration = values
        self.manager.add_usage_log(
            facility_name=facility_name, facility_type=facility_type,
            date_str=date_str, user_name=user_name,
            purpose=purpose, duration_hours=duration)

    def _submit_maintenance_record(self, values):
        (facility_name, facility_type, date_str, condition,
         technician, next_service, maintenance_status) = values
        self.manager.add_maintenance_record(
            facility_name=facility_name, facility_type=facility_type,
            date_str=date_str, condition_status=condition,
            technician=technician, next_service_date=next_service,
            maintenance_status=maintenance_status or "Not Required")

    # ---- edit / delete ---------------------------------------------------
    def _edit_remarks(self):
        if self.selected_record is None:
            messagebox.showinfo("No selection", "Please select a record first.")
            return
        new_text = simpledialog.askstring("Edit remarks", "New remarks:",
                                           initialvalue=self.selected_record.remarks)
        if new_text is None:
            return
        try:
            self.manager.update_remarks(self.selected_record.record_id, new_text)
            self._apply_filters()
            self._select_row(self.selected_record.record_id)
        except InvalidRecordError as err:
            messagebox.showerror("Error", str(err))

    def _update_condition(self):
        record = self.selected_record
        if record is None or not isinstance(record, MaintenanceRecord):
            messagebox.showinfo("Not applicable", "Select a maintenance record first.")
            return
        new_status = simpledialog.askstring(
            "Update condition", f"New condition {CONDITION_STATUSES}:",
            initialvalue=record.condition_status)
        if new_status is None:
            return
        try:
            self.manager.update_condition(record.record_id, new_status)
            self._apply_filters()
            self._select_row(record.record_id)
        except InvalidRecordError as err:
            messagebox.showerror("Error", str(err))

    def _update_maintenance_status(self):
        record = self.selected_record
        if record is None or not isinstance(record, MaintenanceRecord):
            messagebox.showinfo("Not applicable", "Select a maintenance record first.")
            return
        new_status = simpledialog.askstring(
            "Update maintenance status", f"New status {MAINTENANCE_STATUSES}:",
            initialvalue=record.maintenance_status)
        if new_status is None:
            return
        try:
            self.manager.update_maintenance_status(record.record_id, new_status)
            self._apply_filters()
            self._select_row(record.record_id)
        except InvalidRecordError as err:
            messagebox.showerror("Error", str(err))

    def _delete_selected(self):
        record_id = self._selected_id()
        if record_id is None:
            return
        if messagebox.askyesno("Confirm", f"Delete record {record_id}?"):
            try:
                self.manager.delete(record_id)
                self._select_row(None)
                self._apply_filters()
            except InvalidRecordError as err:
                messagebox.showerror("Error", str(err))

    def _show_summary(self):
        summary = self.manager.condition_summary()
        lines = [f"{status}: {count}" for status, count in summary.items()]
        messagebox.showinfo("Condition Summary", "\n".join(lines))

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV file", "*.csv")],
            initialfile="facility_records_export.csv")
        if not path:
            return
        try:
            self.manager.export_csv(path)
            messagebox.showinfo("Exported", f"Records exported to:\n{path}")
        except InvalidRecordError as err:
            messagebox.showerror("Error", str(err))


# ----------------------------------------------------------------------
# Standalone runner
# ----------------------------------------------------------------------
def main():
    root = tk.Tk()
    root.title("University Facilities Booking App - Facility Usage & Maintenance")
    root.geometry("1180x760")
    root.configure(bg=PALETTE["bg"])
    frame = FacilityUsageMaintenanceFrame(root)
    frame.pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
