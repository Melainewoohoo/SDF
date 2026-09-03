import json
import os
from datetime import date, timedelta
from tkinter import Button, Frame, Label, Listbox, OptionMenu, Scrollbar, StringVar, END, messagebox


RESERVATION_FILE = "room_reservations.json"
ROOMS = ["Discussion Room 1", "Discussion Room 2", "Lecture Hall", "Computer Laboratory"]
TIME_OPTIONS = [f"{hour:02d}:00" for hour in range(8, 22)]


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


def booking_page(window, student_data, back_command):
    """Display the student reservation page in the existing Tk window."""
    for widget in window.winfo_children():
        widget.destroy()

    window.geometry("925x500+300+200")
    window.configure(bg="#ffffff")
    window.title("Student Room Reservation")

    Label(window, text="Room Reservation", fg="#57a1f8", bg="#ffffff",
          font=("Microsoft YaHei UI Light", 20, "bold")).place(x=340, y=30)
    Label(window, text=f"Student: {student_data['Name']}  |  ID: {student_data['ID']}",
          fg="#444444", bg="#ffffff",
          font=("Microsoft YaHei UI Light", 11)).place(x=330, y=75)

    form = Frame(window, width=560, height=315, bg="#f7f9fc", highlightthickness=1,
                 highlightbackground="#d8e3ef")
    form.place(x=180, y=115)

    available_dates = [
        (date.today() + timedelta(days=offset)).strftime("%Y-%m-%d")
        for offset in range(30)
    ]
    room_var = StringVar(window, value=ROOMS[0])
    date_var = StringVar(window, value=available_dates[0])
    start_var = StringVar(window, value=TIME_OPTIONS[0])
    end_var = StringVar(window, value=TIME_OPTIONS[1])

    fields = (
        ("Room", room_var, ROOMS, 35),
        ("Booking Date", date_var, available_dates, 95),
        ("Start Time", start_var, TIME_OPTIONS[:-1], 155),
        ("End Time", end_var, TIME_OPTIONS[1:], 215),
    )
    for label_text, variable, options, y_position in fields:
        Label(form, text=label_text, bg="#f7f9fc", fg="#222222",
              font=("Microsoft YaHei UI Light", 11, "bold")).place(x=45, y=y_position)
        dropdown = OptionMenu(form, variable, *options)
        dropdown.configure(width=25, bg="#ffffff", activebackground="#e8f2ff",
                           font=("Microsoft YaHei UI Light", 10), relief="solid", bd=1)
        dropdown.place(x=225, y=y_position - 5)

    def submit_reservation():
        start_time = start_var.get()
        end_time = end_var.get()
        if start_time >= end_time:
            messagebox.showerror("Invalid Time", "End time must be later than start time.")
            return

        reservations = _load_reservations()
        for reservation in reservations:
            same_room_and_date = (
                reservation.get("room") == room_var.get()
                and reservation.get("booking_date") == date_var.get()
            )
            overlaps = (start_time < reservation.get("end_time", "")
                        and end_time > reservation.get("start_time", ""))
            if same_room_and_date and overlaps:
                messagebox.showerror(
                    "Room Unavailable",
                    "This room is already reserved during the selected time.",
                )
                return

        reservations.append({
            "student_id": student_data["ID"],
            "student_name": student_data["Name"],
            "room": room_var.get(),
            "booking_date": date_var.get(),
            "start_time": start_time,
            "end_time": end_time,
            "status": "Reserved",
        })
        try:
            _save_reservations(reservations)
        except OSError as error:
            messagebox.showerror("Save Failed", f"The reservation could not be saved:\n{error}")
            return

        messagebox.showinfo(
            "Reservation Confirmed",
            f"{room_var.get()} reserved for {date_var.get()}\n"
            f"from {start_time} to {end_time}.",
        )

    Button(form, text="Confirm Reservation", command=submit_reservation,
           bg="#57a1f8", fg="#ffffff", activebackground="#368ad5",
           activeforeground="#ffffff", font=("Microsoft YaHei UI Light", 10, "bold"),
           width=19).place(x=205, y=270)
    Button(window, text="Back", command=back_command,
           font=("Microsoft YaHei UI Light", 10), width=10).place(x=180, y=450)


def booking_history_page(window, student_data, back_command):
    """Show reservations belonging to the currently logged-in student."""
    for widget in window.winfo_children():
        widget.destroy()

    window.geometry("925x500+300+200")
    window.configure(bg="#ffffff")
    window.title("My Booking History")

    Label(window, text="My Booking History", fg="#57a1f8", bg="#ffffff",
          font=("Microsoft YaHei UI Light", 20, "bold")).place(x=330, y=30)
    Label(window, text=f"Student: {student_data['Name']}  |  ID: {student_data['ID']}",
          fg="#444444", bg="#ffffff",
          font=("Microsoft YaHei UI Light", 11)).place(x=330, y=75)

    history_frame = Frame(window, width=700, height=315, bg="#f7f9fc",
                          highlightthickness=1, highlightbackground="#d8e3ef")
    history_frame.place(x=110, y=115)

    student_bookings = [
        reservation for reservation in _load_reservations()
        if str(reservation.get("student_id")) == str(student_data["ID"])
    ]
    student_bookings.sort(
        key=lambda reservation: (
            reservation.get("booking_date", ""),
            reservation.get("start_time", ""),
        ),
        reverse=True,
    )

    if not student_bookings:
        Label(history_frame, text="You have not booked any facility yet.",
              fg="#555555", bg="#f7f9fc",
              font=("Microsoft YaHei UI Light", 13)).place(x=195, y=135)
    else:
        Label(history_frame, text="Room / Facility", bg="#f7f9fc", fg="#222222",
              font=("Microsoft YaHei UI Light", 10, "bold")).place(x=25, y=18)
        Label(history_frame, text="Date", bg="#f7f9fc", fg="#222222",
              font=("Microsoft YaHei UI Light", 10, "bold")).place(x=275, y=18)
        Label(history_frame, text="Time", bg="#f7f9fc", fg="#222222",
              font=("Microsoft YaHei UI Light", 10, "bold")).place(x=410, y=18)
        Label(history_frame, text="Status", bg="#f7f9fc", fg="#222222",
              font=("Microsoft YaHei UI Light", 10, "bold")).place(x=585, y=18)

        scrollbar = Scrollbar(history_frame, orient="vertical")
        scrollbar.place(x=660, y=50, height=235)
        booking_list = Listbox(
            history_frame,
            width=91,
            height=13,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10),
            bg="#ffffff",
            fg="#222222",
            selectbackground="#dceeff",
            relief="solid",
            bd=1,
        )
        booking_list.place(x=25, y=50)
        scrollbar.configure(command=booking_list.yview)

        for reservation in student_bookings:
            room = reservation.get("room", "Unknown")[:27]
            booking_date = reservation.get("booking_date", "-")
            time_range = (f"{reservation.get('start_time', '-')} - "
                          f"{reservation.get('end_time', '-')}")
            status = reservation.get("status", "Reserved")
            booking_list.insert(
                END,
                f"{room:<28}{booking_date:<14}{time_range:<19}{status}",
            )

    Button(window, text="Back", command=back_command,
           font=("Microsoft YaHei UI Light", 10), width=10).place(x=110, y=450)
