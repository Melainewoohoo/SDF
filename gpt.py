# ============================================================
# BMCS1033 - University Facilities Booking App
# Module: Facility Usage & Maintenance Management
# Author: NEO AI YIK
# ============================================================

import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
from datetime import datetime


# ============================================================
# Base Class
# Demonstrates inheritance
# ============================================================

class BaseRecord:
    def __init__(self, facility_id):
        self.facility_id = facility_id.strip().upper()


# ============================================================
# Facility Record Class
# Inherits from BaseRecord
# Demonstrates encapsulation
# ============================================================

class FacilityRecord(BaseRecord):

    def __init__(self, facility_id, usage, condition, date):
        super().__init__(facility_id)

        self.__usage = usage.strip()
        self.__condition = condition.strip()
        self.__date = date.strip()

    # Getter methods
    def get_usage(self):
        return self.__usage

    def get_condition(self):
        return self.__condition

    def get_date(self):
        return self.__date

    # Setter method
    def set_condition(self, condition):
        self.__condition = condition.strip()

    # Convert object to dictionary
    def to_dict(self):
        return {
            "facility_id": self.facility_id,
            "usage": self.__usage,
            "condition": self.__condition,
            "date": self.__date
        }


# ============================================================
# Facility Usage & Maintenance Management
# ============================================================

class FacilityManager:

    FILE_NAME = "facility_records.csv"

    # Tuple
    VALID_CONDITIONS = (
        "Good",
        "Fair",
        "Needs Repair",
        "Under Maintenance"
    )

    def __init__(self):
        # Encapsulation: private collection
        self.__records = []

        # Set
        self.__facility_ids = set()

        # Load existing records
        self.load_records()

    # ========================================================
    # File Processing - Read
    # ========================================================

    def load_records(self):

        if not os.path.exists(self.FILE_NAME):
            return

        try:
            with open(self.FILE_NAME, "r", newline="", encoding="utf-8") as file:

                reader = csv.DictReader(file)

                for row in reader:

                    record = FacilityRecord(
                        row["facility_id"],
                        row["usage"],
                        row["condition"],
                        row["date"]
                    )

                    self.__records.append(record)
                    self.__facility_ids.add(record.facility_id)

        except (FileNotFoundError, KeyError, csv.Error) as error:
            print("Error loading records:", error)

    # ========================================================
    # File Processing - Write
    # ========================================================

    def save_records(self):

        try:
            with open(
                self.FILE_NAME,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                fieldnames = [
                    "facility_id",
                    "usage",
                    "condition",
                    "date"
                ]

                writer = csv.DictWriter(
                    file,
                    fieldnames=fieldnames
                )

                writer.writeheader()

                for record in self.__records:
                    writer.writerow(record.to_dict())

        except IOError as error:
            raise IOError(
                "Unable to save records: " + str(error)
            )

    # ========================================================
    # Add Record
    # ========================================================

    def add_record(self, facility_id, usage, condition):

        facility_id = facility_id.strip().upper()
        usage = usage.strip()
        condition = condition.strip()

        # String processing
        if not facility_id:
            raise ValueError("Facility ID cannot be empty.")

        if not usage:
            raise ValueError("Usage description cannot be empty.")

        if condition not in self.VALID_CONDITIONS:
            raise ValueError("Invalid maintenance condition.")

        # Check duplicate facility ID
        if facility_id in self.__facility_ids:
            raise ValueError(
                "A record for this Facility ID already exists."
            )

        # Current date
        date = datetime.now().strftime("%Y-%m-%d")

        record = FacilityRecord(
            facility_id,
            usage,
            condition,
            date
        )

        self.__records.append(record)
        self.__facility_ids.add(facility_id)

        self.save_records()

    # ========================================================
    # Search Record
    # ========================================================

    def find_record(self, facility_id):

        facility_id = facility_id.strip().upper()

        for record in self.__records:

            if record.facility_id == facility_id:
                return record

        return None

    # ========================================================
    # Update Maintenance Condition
    # ========================================================

    def update_record(self, facility_id, new_condition):

        record = self.find_record(facility_id)

        if record is None:
            return False

        if new_condition not in self.VALID_CONDITIONS:
            raise ValueError("Invalid maintenance condition.")

        record.set_condition(new_condition)

        self.save_records()

        return True

    # ========================================================
    # Delete Record
    # ========================================================

    def delete_record(self, facility_id):

        record = self.find_record(facility_id)

        if record is None:
            return False

        self.__records.remove(record)
        self.__facility_ids.remove(record.facility_id)

        self.save_records()

        return True


# ============================================================
# GUI Class
# ============================================================

class FacilityGUI:

    def __init__(self, root):

        self.root = root
        self.root.title(
            "Facility Usage & Maintenance Management"
        )
        self.root.geometry("700x550")

        self.manager = FacilityManager()

        self.create_widgets()

    # ========================================================
    # GUI
    # ========================================================

    def create_widgets(self):

        title = tk.Label(
            self.root,
            text="Facility Usage & Maintenance Management",
            font=("Arial", 18, "bold")
        )

        title.pack(pady=20)

        # Main menu
        menu_frame = tk.Frame(self.root)
        menu_frame.pack(pady=10)

        tk.Button(
            menu_frame,
            text="1. Add Record",
            width=25,
            command=self.add_window
        ).pack(pady=5)

        tk.Button(
            menu_frame,
            text="2. View/Search Record",
            width=25,
            command=self.view_window
        ).pack(pady=5)

        tk.Button(
            menu_frame,
            text="3. Update Condition",
            width=25,
            command=self.update_window
        ).pack(pady=5)

        tk.Button(
            menu_frame,
            text="4. Delete Record",
            width=25,
            command=self.delete_window
        ).pack(pady=5)

        tk.Button(
            menu_frame,
            text="5. Exit",
            width=25,
            command=self.root.destroy
        ).pack(pady=5)

    # ========================================================
    # Choice 1 - Add Record
    # ========================================================

    def add_window(self):

        window = tk.Toplevel(self.root)
        window.title("Add Usage/Maintenance Record")
        window.geometry("450x350")

        tk.Label(
            window,
            text="Facility ID:"
        ).pack(pady=5)

        facility_entry = tk.Entry(window)
        facility_entry.pack()

        tk.Label(
            window,
            text="Usage Description:"
        ).pack(pady=5)

        usage_entry = tk.Entry(window, width=40)
        usage_entry.pack()

        tk.Label(
            window,
            text="Maintenance Condition:"
        ).pack(pady=5)

        condition_combo = ttk.Combobox(
            window,
            values=FacilityManager.VALID_CONDITIONS,
            state="readonly"
        )

        condition_combo.pack()

        def save():

            try:

                self.manager.add_record(
                    facility_entry.get(),
                    usage_entry.get(),
                    condition_combo.get()
                )

                messagebox.showinfo(
                    "Success",
                    "Record added successfully."
                )

                window.destroy()

            except ValueError as error:

                messagebox.showerror(
                    "Error",
                    str(error)
                )

            except IOError as error:

                messagebox.showerror(
                    "File Error",
                    str(error)
                )

        tk.Button(
            window,
            text="Save Record",
            command=save
        ).pack(pady=20)

    # ========================================================
    # Choice 2 - View/Search Record
    # ========================================================

    def view_window(self):

        window = tk.Toplevel(self.root)
        window.title("View/Search Record")
        window.geometry("500x350")

        tk.Label(
            window,
            text="Enter Facility ID:"
        ).pack(pady=10)

        facility_entry = tk.Entry(window)
        facility_entry.pack()

        result_label = tk.Label(
            window,
            text="",
            justify="left",
            font=("Arial", 11)
        )

        result_label.pack(pady=30)

        def search():

            facility_id = facility_entry.get()

            record = self.manager.find_record(
                facility_id
            )

            if record is not None:

                result_label.config(
                    text=
                    f"Facility ID: {record.facility_id}\n"
                    f"Usage: {record.get_usage()}\n"
                    f"Condition: {record.get_condition()}\n"
                    f"Date: {record.get_date()}"
                )

            else:

                result_label.config(
                    text="Record not found."
                )

        tk.Button(
            window,
            text="Search",
            command=search
        ).pack()

    # ========================================================
    # Choice 3 - Update Maintenance Condition
    # ========================================================

    def update_window(self):

        window = tk.Toplevel(self.root)
        window.title("Update Maintenance Condition")
        window.geometry("450x300")

        tk.Label(
            window,
            text="Enter Facility ID:"
        ).pack(pady=10)

        facility_entry = tk.Entry(window)
        facility_entry.pack()

        tk.Label(
            window,
            text="New Condition:"
        ).pack(pady=10)

        condition_combo = ttk.Combobox(
            window,
            values=FacilityManager.VALID_CONDITIONS,
            state="readonly"
        )

        condition_combo.pack()

        def update():

            try:

                facility_id = facility_entry.get()
                condition = condition_combo.get()

                record = self.manager.find_record(
                    facility_id
                )

                if record is None:

                    messagebox.showerror(
                        "Error",
                        "Record not found."
                    )

                    return

                self.manager.update_record(
                    facility_id,
                    condition
                )

                messagebox.showinfo(
                    "Success",
                    "Record updated successfully."
                )

                window.destroy()

            except ValueError as error:

                messagebox.showerror(
                    "Error",
                    str(error)
                )

            except IOError as error:

                messagebox.showerror(
                    "File Error",
                    str(error)
                )

        tk.Button(
            window,
            text="Update and Save",
            command=update
        ).pack(pady=20)

    # ========================================================
    # Choice 4 - Delete Record
    # ========================================================

    def delete_window(self):

        window = tk.Toplevel(self.root)
        window.title("Delete Record")
        window.geometry("400x250")

        tk.Label(
            window,
            text="Enter Facility ID:"
        ).pack(pady=20)

        facility_entry = tk.Entry(window)
        facility_entry.pack()

        def delete():

            facility_id = facility_entry.get()

            record = self.manager.find_record(
                facility_id
            )

            if record is None:

                messagebox.showerror(
                    "Error",
                    "Record not found."
                )

                return

            # Confirmation
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                "Are you sure you want to delete this record?"
            )

            if confirm:

                try:

                    self.manager.delete_record(
                        facility_id
                    )

                    messagebox.showinfo(
                        "Success",
                        "Record deleted successfully."
                    )

                    window.destroy()

                except IOError as error:

                    messagebox.showerror(
                        "File Error",
                        str(error)
                    )

        tk.Button(
            window,
            text="Delete Record",
            command=delete
        ).pack(pady=20)


# ============================================================
# Main Program
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = FacilityGUI(root)

    root.mainloop()