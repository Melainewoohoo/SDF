import json
import os
from datetime import date, timedelta
from tkinter import (Button, Checkbutton, Entry, Frame, IntVar, Label, Listbox,
                     OptionMenu, Scrollbar, StringVar, Text, END, messagebox)


RESERVATION_FILE = "room_reservations.json"
ROOM_FILE = "rooms.json"
ROOMS = ["Discussion Room 1", "Discussion Room 2", "Lecture Hall", "Computer Laboratory"]

# Fixed weekly schedule for every room.
# Each item contains the day, start time and end time.
ROOM_SCHEDULE = {
    "Discussion Room 1": [
        ("Monday", "09:00", "10:00"),
        ("Monday", "14:00", "15:00"),
        ("Wednesday", "10:00", "11:00"),
        ("Friday", "15:00", "16:00"),
    ],
    "Discussion Room 2": [
        ("Tuesday", "09:00", "10:00"),
        ("Tuesday", "13:00", "14:00"),
        ("Thursday", "11:00", "12:00"),
        ("Friday", "10:00", "11:00"),
    ],
    "Lecture Hall": [
        ("Monday", "11:00", "13:00"),
        ("Wednesday", "14:00", "16:00"),
        ("Friday", "09:00", "11:00"),
    ],
    "Computer Laboratory": [
        ("Tuesday", "10:00", "12:00"),
        ("Wednesday", "09:00", "11:00"),
        ("Thursday", "14:00", "16:00"),
    ],
}

# A newly added room uses these fixed slots until its own schedule is added.
DEFAULT_ROOM_SCHEDULE = [
    ("Monday", "09:00", "10:00"),
    ("Tuesday", "11:00", "12:00"),
    ("Wednesday", "14:00", "15:00"),
    ("Thursday", "10:00", "11:00"),
    ("Friday", "15:00", "16:00"),
]

TERMS_TEXT = """Terms of use:

1. Discussion rooms are for study purposes only.
2. Do not hog the classroom if it is not in use.
3. Foods and beverages are prohibited in the discussion room.
4. Room booked will be forfeited after 10 minutes if no-show.
5. Students shall discuss softly so as not to disturb other users.
6. Remember to take all your belongings with you when you leave the room.
7. Always keep the room clean.
8. Do not add, move, or remove the furniture inside the discussion room.
9. No vandalism is allowed inside the discussion room.

NOTE 1: Discussion rooms are strictly to be used for academic purposes only.

NOTE 2: Projecting movies from the projector is prohibited due to copyright issues."""


def _load_reservations():
    if not os.path.exists(RESERVATION_FILE):
        return []
    try:
        with open(RESERVATION_FILE, "r", encoding="utf-8") as file:
            saved_data = json.load(file)
            return saved_data if isinstance(saved_data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save_reservations(reservations):
    with open(RESERVATION_FILE, "w", encoding="utf-8") as file:
        json.dump(reservations, file, indent=4)


def load_available_rooms():
    # Read the rooms created by staff in the Manage Room page.
    if not os.path.exists(ROOM_FILE):
        return ROOMS

    try:
        with open(ROOM_FILE, "r", encoding="utf-8") as file:
            room_records = json.load(file)
    except (OSError, json.JSONDecodeError):
        return ROOMS

    available_rooms = []
    for room in room_records:
        if room.get("status") == "Available":
            available_rooms.append(room.get("room_name"))

    return available_rooms


def booking_page(window, student_data, back_command):
    # Display the student reservation page.
    for widget in window.winfo_children():
        widget.destroy()

    window.geometry("925x500+300+200")
    window.configure(bg="#ffffff")
    window.title("Student Room Reservation")

    Label(window, text="Room Reservation", fg="#57a1f8", bg="#ffffff",
          font=("Microsoft YaHei UI Light", 18, "bold")).place(x=350, y=12)
    Label(window, text=f"Student: {student_data['Name']}  |  ID: {student_data['ID']}",
          fg="#444444", bg="#ffffff",
          font=("Microsoft YaHei UI Light", 10)).place(x=345, y=52)

    form = Frame(window, width=875, height=355, bg="#f7f9fc", highlightthickness=1,
                 highlightbackground="#d8e3ef")
    form.place(x=25, y=85)

    available_dates = []
    for offset in range(14):
        booking_date = date.today() + timedelta(days=offset)
        available_dates.append(booking_date.strftime("%Y-%m-%d"))

    booking_rooms = load_available_rooms()
    if len(booking_rooms) == 0:
        booking_rooms = ["No rooms available"]

    room_var = StringVar(window, value=booking_rooms[0])
    date_var = StringVar(window, value="All Dates")
    pax_var = StringVar(window, value="1")
    agreed_var = IntVar(window, value=0)
    member_entries = []

    Label(form, text="Room", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=15, y=15)
    OptionMenu(form, room_var, *booking_rooms).place(x=70, y=10, width=205)

    Label(form, text="Date", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=15, y=50)
    OptionMenu(form, date_var, "All Dates", *available_dates).place(x=70, y=45, width=145)

    Label(form, text="Available Date and Time", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=15, y=85)
    available_list = Listbox(form, width=48, height=5, font=("Consolas", 9),
                             bg="#ffffff", selectbackground="#57a1f8")
    available_list.place(x=15, y=110)

    Label(form, text="Number of Pax (maximum 6, including you)", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 9, "bold")).place(x=15, y=205)
    pax_menu = OptionMenu(form, pax_var, "1", "2", "3", "4", "5", "6")
    pax_menu.place(x=285, y=198, width=65)

    Label(form, text="Member Student ID", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 8, "bold")).place(x=15, y=238)
    Label(form, text="Member Name", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 8, "bold")).place(x=180, y=238)

    member_frame = Frame(form, width=420, height=100, bg="#f7f9fc")
    member_frame.place(x=15, y=258)

    def show_member_fields(selected_pax):
        for widget in member_frame.winfo_children():
            widget.destroy()
        member_entries.clear()

        number_of_members = int(selected_pax) - 1
        for member_number in range(number_of_members):
            id_entry = Entry(member_frame, width=20)
            id_entry.place(x=0, y=member_number * 20)
            name_entry = Entry(member_frame, width=22)
            name_entry.place(x=165, y=member_number * 20)
            member_entries.append((id_entry, name_entry))

    pax_menu["menu"].delete(0, END)
    for pax in range(1, 7):
        pax_menu["menu"].add_command(
            label=str(pax),
            command=lambda value=str(pax): (pax_var.set(value), show_member_fields(value)),
        )

    Label(form, text="Booking Guidelines", bg="#f7f9fc", fg="#222222",
          font=("Microsoft YaHei UI Light", 11, "bold")).place(x=455, y=12)
    terms_box = Text(form, width=48, height=16, wrap="word",
                     font=("Microsoft YaHei UI Light", 8), bg="#ffffff")
    terms_box.place(x=455, y=40)
    terms_scrollbar = Scrollbar(form, orient="vertical", command=terms_box.yview)
    terms_scrollbar.place(x=840, y=40, height=252)
    terms_box.configure(yscrollcommand=terms_scrollbar.set)
    terms_box.insert("1.0", TERMS_TEXT)
    terms_box.configure(state="disabled")

    Checkbutton(form, text="I have read and agreed to the terms of use",
                variable=agreed_var, bg="#f7f9fc",
                font=("Microsoft YaHei UI Light", 9)).place(x=455, y=295)

    def search_available_slots():
        available_list.delete(0, END)
        selected_room = room_var.get()
        selected_date = date_var.get()
        reservations = _load_reservations()

        if selected_room == "No rooms available":
            available_list.insert(END, "No rooms are currently available.")
            return

        if selected_room in ROOM_SCHEDULE:
            selected_schedule = ROOM_SCHEDULE[selected_room]
        else:
            selected_schedule = DEFAULT_ROOM_SCHEDULE

        for booking_date in available_dates:
            if selected_date != "All Dates" and selected_date != booking_date:
                continue

            day_name = date.fromisoformat(booking_date).strftime("%A")
            for schedule in selected_schedule:
                schedule_day = schedule[0]
                start_time = schedule[1]
                end_time = schedule[2]

                if schedule_day == day_name:
                    slot_is_booked = False
                    for reservation in reservations:
                        if (reservation.get("room") == selected_room
                                and reservation.get("booking_date") == booking_date
                                and reservation.get("start_time") == start_time
                                and reservation.get("end_time") == end_time):
                            slot_is_booked = True

                    if not slot_is_booked:
                        available_list.insert(
                            END, booking_date + "  |  " + start_time + " - " + end_time
                        )

        if available_list.size() == 0:
            available_list.insert(END, "No available time for this search.")

    def submit_reservation():
        selected = available_list.curselection()
        if (not selected
                or available_list.get(selected[0]).startswith("No available")
                or available_list.get(selected[0]).startswith("No rooms")):
            messagebox.showerror("No Selection", "Please select an available date and time.")
            return

        if agreed_var.get() == 0:
            messagebox.showerror(
                "Terms Not Accepted",
                "You must read and agree to the terms of use before booking.",
            )
            return

        members = []
        used_ids = [str(student_data["ID"])]
        for id_entry, name_entry in member_entries:
            member_id = id_entry.get().strip()
            member_name = name_entry.get().strip()

            if member_id == "" or member_name == "":
                messagebox.showerror("Missing Member Details",
                                     "Please enter the student ID and name for every member.")
                return
            if not member_id.isdigit():
                messagebox.showerror("Invalid Student ID", "Student ID must contain numbers only.")
                return
            if member_id in used_ids:
                messagebox.showerror("Duplicate Student ID",
                                     "Each group member must have a different student ID.")
                return

            used_ids.append(member_id)
            members.append({"student_id": member_id, "student_name": member_name})

        selected_slot = available_list.get(selected[0])
        parts = selected_slot.split("  |  ")
        booking_date = parts[0]
        time_parts = parts[1].split(" - ")
        start_time = time_parts[0]
        end_time = time_parts[1]

        reservations = _load_reservations()
        reservations.append({
            "student_id": student_data["ID"],
            "student_name": student_data["Name"],
            "room": room_var.get(),
            "booking_date": booking_date,
            "start_time": start_time,
            "end_time": end_time,
            "number_of_pax": int(pax_var.get()),
            "members": members,
            "status": "Reserved",
        })

        try:
            _save_reservations(reservations)
        except OSError as error:
            messagebox.showerror("Save Failed", f"The reservation could not be saved:\n{error}")
            return

        messagebox.showinfo("Reservation Confirmed",
                            f"{room_var.get()} reserved for {booking_date}\n"
                            f"from {start_time} to {end_time}.")
        search_available_slots()

    Button(form, text="Search Available", command=search_available_slots,
           bg="#57a1f8", fg="#ffffff", font=("Microsoft YaHei UI Light", 9, "bold"),
           width=15).place(x=235, y=45)
    Button(form, text="Book Selected Slot", command=submit_reservation,
           bg="#57a1f8", fg="#ffffff", font=("Microsoft YaHei UI Light", 9, "bold"),
           width=18).place(x=700, y=320)
    Button(window, text="Back", command=back_command,
           font=("Microsoft YaHei UI Light", 10), width=10).place(x=25, y=455)

    show_member_fields("1")
    search_available_slots()


def booking_history_page(window, student_data, back_command):
    # Show reservations belonging to the currently logged-in student.
    for widget in window.winfo_children():
        widget.destroy()

    window.geometry("925x500+300+200")
    window.configure(bg="#ffffff")
    window.title("My Booking")

    Label(window, text="My Booking", fg="#57a1f8", bg="#ffffff",
          font=("Microsoft YaHei UI Light", 20, "bold")).place(x=330, y=30)
    Label(window, text=f"Student: {student_data['Name']}  |  ID: {student_data['ID']}",
          fg="#444444", bg="#ffffff",
          font=("Microsoft YaHei UI Light", 11)).place(x=330, y=75)

    history_frame = Frame(window, width=700, height=315, bg="#f7f9fc",
                          highlightthickness=1, highlightbackground="#d8e3ef")
    history_frame.place(x=110, y=115)

    Label(history_frame, text="Room / Facility", bg="#f7f9fc", fg="#222222",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=25, y=15)
    Label(history_frame, text="Date", bg="#f7f9fc", fg="#222222",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=265, y=15)
    Label(history_frame, text="Time", bg="#f7f9fc", fg="#222222",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=390, y=15)
    Label(history_frame, text="Status", bg="#f7f9fc", fg="#222222",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=555, y=15)

    scrollbar = Scrollbar(history_frame, orient="vertical")
    scrollbar.place(x=660, y=45, height=180)
    booking_list = Listbox(
        history_frame,
        width=91,
        height=10,
        yscrollcommand=scrollbar.set,
        font=("Consolas", 10),
        bg="#ffffff",
        fg="#222222",
        selectbackground="#57a1f8",
        relief="solid",
        bd=1,
    )
    booking_list.place(x=25, y=45)
    scrollbar.configure(command=booking_list.yview)

    empty_message = Label(history_frame, text="", fg="#555555", bg="#f7f9fc",
                          font=("Microsoft YaHei UI Light", 11))
    empty_message.place(x=220, y=230)
    student_bookings = []

    def refresh_booking_history():
        booking_list.delete(0, END)
        student_bookings.clear()

        reservations = _load_reservations()
        for reservation in reservations:
            if str(reservation.get("student_id")) == str(student_data["ID"]):
                student_bookings.append(reservation)

        student_bookings.sort(
            key=lambda item: (item.get("booking_date", ""), item.get("start_time", "")),
            reverse=True,
        )

        for reservation in student_bookings:
            room = reservation.get("room", "Unknown")[:25]
            booking_date = reservation.get("booking_date", "-")
            time_range = (reservation.get("start_time", "-") + " - "
                          + reservation.get("end_time", "-"))
            status = reservation.get("status", "Reserved")
            booking_list.insert(
                END,
                f"{room:<26}{booking_date:<13}{time_range:<18}{status}",
            )

        if len(student_bookings) == 0:
            empty_message.configure(text="You have not booked any facility yet.")
        else:
            empty_message.configure(text="Select one booking before choosing an action.")

    def get_selected_booking():
        selected = booking_list.curselection()
        if not selected:
            messagebox.showerror("No Booking Selected", "Please select a booking first.")
            return None
        return student_bookings[selected[0]]

    def booking_matches(first_booking, second_booking):
        return (str(first_booking.get("student_id")) == str(second_booking.get("student_id"))
                and first_booking.get("room") == second_booking.get("room")
                and first_booking.get("booking_date") == second_booking.get("booking_date")
                and first_booking.get("start_time") == second_booking.get("start_time")
                and first_booking.get("end_time") == second_booking.get("end_time"))

    def change_status(new_status):
        selected_booking = get_selected_booking()
        if selected_booking is None:
            return

        reservations = _load_reservations()
        for reservation in reservations:
            if booking_matches(reservation, selected_booking):
                reservation["status"] = new_status
                break

        try:
            _save_reservations(reservations)
        except OSError as error:
            messagebox.showerror("Update Failed", f"The booking could not be updated:\n{error}")
            return

        messagebox.showinfo("Status Updated", "Booking status updated to " + new_status + ".")
        refresh_booking_history()

    def check_in_booking():
        selected_booking = get_selected_booking()
        if selected_booking is None:
            return

        status = selected_booking.get("status", "Reserved")
        if status != "Reserved":
            messagebox.showerror("Check In Not Allowed",
                                 "Only a reserved booking can be checked in.")
            return
        change_status("Checked In")

    def check_out_booking():
        selected_booking = get_selected_booking()
        if selected_booking is None:
            return

        status = selected_booking.get("status", "Reserved")
        if status == "Reserved":
            messagebox.showerror("Check Out Not Allowed",
                                 "You must check in before you can check out.")
            return
        if status != "Checked In":
            messagebox.showerror("Check Out Not Allowed",
                                 "This booking has already been completed.")
            return
        change_status("Checked Out")

    def cancel_booking():
        selected_booking = get_selected_booking()
        if selected_booking is None:
            return

        if selected_booking.get("status", "Reserved") != "Reserved":
            messagebox.showerror("Cancellation Not Allowed",
                                 "Only a reserved booking can be cancelled.")
            return

        details = (
            "Room: " + selected_booking.get("room", "-") + "\n"
            "Date: " + selected_booking.get("booking_date", "-") + "\n"
            "Time: " + selected_booking.get("start_time", "-") + " - "
            + selected_booking.get("end_time", "-") + "\n"
            "Pax: " + str(selected_booking.get("number_of_pax", 1)) + "\n\n"
            "Are you sure you want to cancel this booking?"
        )
        confirm_cancel = messagebox.askyesno("Confirm Cancellation", details)
        if not confirm_cancel:
            return

        reservations = _load_reservations()
        updated_reservations = []
        booking_removed = False
        for reservation in reservations:
            if not booking_removed and booking_matches(reservation, selected_booking):
                booking_removed = True
            else:
                updated_reservations.append(reservation)

        try:
            _save_reservations(updated_reservations)
        except OSError as error:
            messagebox.showerror("Cancellation Failed",
                                 f"The booking could not be cancelled:\n{error}")
            return

        messagebox.showinfo("Booking Cancelled", "Your booking has been cancelled.")
        refresh_booking_history()

    Button(history_frame, text="Check In", command=check_in_booking,
           bg="#57a1f8", fg="#ffffff", width=13).place(x=25, y=270)
    Button(history_frame, text="Check Out", command=check_out_booking,
           bg="#57a1f8", fg="#ffffff", width=13).place(x=155, y=270)
    Button(history_frame, text="Cancel Booking", command=cancel_booking,
           bg="#d9534f", fg="#ffffff", width=15).place(x=285, y=270)

    refresh_booking_history()

    Button(window, text="Back", command=back_command,
           font=("Microsoft YaHei UI Light", 10), width=10).place(x=110, y=450)