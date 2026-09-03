import json
import os
from tkinter import (Button, Entry, Frame, Label, Listbox, OptionMenu,
                     Scrollbar, StringVar, END, messagebox)


ROOM_FILE = "rooms.json"


def load_rooms():
    if not os.path.exists(ROOM_FILE):
        return []

    try:
        with open(ROOM_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return []


def save_rooms(rooms):
    with open(ROOM_FILE, "w", encoding="utf-8") as file:
        json.dump(rooms, file, indent=4)


def manage_room_page(window, back_command):
    for widget in window.winfo_children():
        widget.destroy()

    window.geometry("925x500+300+200")
    window.configure(bg="#ffffff")
    window.title("Manage Room")

    Label(window, text="Manage Room", fg="#57a1f8", bg="#ffffff",
          font=("Microsoft YaHei UI Light", 20, "bold")).place(x=370, y=25)

    form = Frame(window, width=330, height=340, bg="#f7f9fc",
                 highlightthickness=1, highlightbackground="#d8e3ef")
    form.place(x=45, y=90)

    Label(form, text="Room ID", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=25, y=25)
    room_id_entry = Entry(form, width=25)
    room_id_entry.place(x=130, y=28)

    Label(form, text="Room Name", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=25, y=75)
    room_name_entry = Entry(form, width=25)
    room_name_entry.place(x=130, y=78)

    Label(form, text="Room Type", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=25, y=125)
    room_type_var = StringVar(window, value="Discussion Room")
    room_type_menu = OptionMenu(
        form,
        room_type_var,
        "Discussion Room",
        "Lecture Hall",
        "Computer Laboratory",
        "Classroom",
    )
    room_type_menu.place(x=130, y=118, width=170)

    Label(form, text="Capacity", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=25, y=175)
    capacity_entry = Entry(form, width=25)
    capacity_entry.place(x=130, y=178)

    Label(form, text="Status", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 10, "bold")).place(x=25, y=225)
    status_var = StringVar(window, value="Available")
    OptionMenu(form, status_var, "Available", "Maintenance", "Unavailable").place(
        x=130, y=218, width=170
    )

    list_frame = Frame(window, width=460, height=340, bg="#f7f9fc",
                       highlightthickness=1, highlightbackground="#d8e3ef")
    list_frame.place(x=420, y=90)

    Label(list_frame, text="Room ID", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 9, "bold")).place(x=15, y=15)
    Label(list_frame, text="Room Name", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 9, "bold")).place(x=95, y=15)
    Label(list_frame, text="Capacity", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 9, "bold")).place(x=275, y=15)
    Label(list_frame, text="Status", bg="#f7f9fc",
          font=("Microsoft YaHei UI Light", 9, "bold")).place(x=350, y=15)

    scrollbar = Scrollbar(list_frame, orient="vertical")
    scrollbar.place(x=425, y=45, height=245)
    room_list = Listbox(list_frame, width=58, height=14,
                        font=("Consolas", 9), yscrollcommand=scrollbar.set)
    room_list.place(x=15, y=45)
    scrollbar.configure(command=room_list.yview)
    displayed_rooms = []

    def clear_fields():
        room_id_entry.delete(0, END)
        room_name_entry.delete(0, END)
        capacity_entry.delete(0, END)
        room_type_var.set("Discussion Room")
        status_var.set("Available")
        room_list.selection_clear(0, END)

    def refresh_room_list():
        room_list.delete(0, END)
        displayed_rooms.clear()
        rooms = load_rooms()

        for room in rooms:
            displayed_rooms.append(room)
            room_list.insert(
                END,
                f"{str(room['room_id']):<10}{room['room_name'][:20]:<21}"
                f"{str(room['capacity']):<9}{room['status']}",
            )

    def get_form_data():
        room_id = room_id_entry.get().strip()
        room_name = room_name_entry.get().strip()
        capacity = capacity_entry.get().strip()

        if room_id == "" or room_name == "" or capacity == "":
            messagebox.showerror("Missing Details", "Please complete all room details.")
            return None
        if not capacity.isdigit() or int(capacity) < 1:
            messagebox.showerror("Invalid Capacity", "Capacity must be a positive number.")
            return None

        return {
            "room_id": room_id,
            "room_name": room_name,
            "room_type": room_type_var.get(),
            "capacity": int(capacity),
            "status": status_var.get(),
        }

    def add_room():
        new_room = get_form_data()
        if new_room is None:
            return

        rooms = load_rooms()
        for room in rooms:
            if str(room["room_id"]) == new_room["room_id"]:
                messagebox.showerror("Duplicate Room ID", "This room ID already exists.")
                return

        rooms.append(new_room)
        save_rooms(rooms)
        messagebox.showinfo("Room Added", "The room has been added successfully.")
        clear_fields()
        refresh_room_list()

    def select_room(event):
        selected = room_list.curselection()
        if not selected:
            return

        room = displayed_rooms[selected[0]]
        clear_fields()
        room_id_entry.insert(0, room["room_id"])
        room_name_entry.insert(0, room["room_name"])
        room_type_var.set(room["room_type"])
        capacity_entry.insert(0, room["capacity"])
        status_var.set(room["status"])
        room_list.selection_set(selected[0])

    def update_room():
        selected = room_list.curselection()
        if not selected:
            messagebox.showerror("No Room Selected", "Please select a room to update.")
            return

        updated_room = get_form_data()
        if updated_room is None:
            return

        original_room_id = str(displayed_rooms[selected[0]]["room_id"])
        rooms = load_rooms()
        for room in rooms:
            if (str(room["room_id"]) == updated_room["room_id"]
                    and str(room["room_id"]) != original_room_id):
                messagebox.showerror("Duplicate Room ID", "This room ID already exists.")
                return

        for number in range(len(rooms)):
            if str(rooms[number]["room_id"]) == original_room_id:
                rooms[number] = updated_room
                break

        save_rooms(rooms)
        messagebox.showinfo("Room Updated", "The room has been updated successfully.")
        clear_fields()
        refresh_room_list()

    def delete_room():
        selected = room_list.curselection()
        if not selected:
            messagebox.showerror("No Room Selected", "Please select a room to delete.")
            return

        room = displayed_rooms[selected[0]]
        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this room?\n\n"
            "Room ID: " + str(room["room_id"]) + "\n"
            "Room Name: " + room["room_name"],
        )
        if not confirm:
            return

        rooms = load_rooms()
        updated_rooms = []
        for saved_room in rooms:
            if str(saved_room["room_id"]) != str(room["room_id"]):
                updated_rooms.append(saved_room)

        save_rooms(updated_rooms)
        messagebox.showinfo("Room Deleted", "The room has been deleted successfully.")
        clear_fields()
        refresh_room_list()

    room_list.bind("<<ListboxSelect>>", select_room)

    Button(form, text="Add", command=add_room, width=8,
           bg="#57a1f8", fg="#ffffff").place(x=20, y=285)
    Button(form, text="Update", command=update_room, width=8,
           bg="#57a1f8", fg="#ffffff").place(x=95, y=285)
    Button(form, text="Delete", command=delete_room, width=8,
           bg="#d9534f", fg="#ffffff").place(x=170, y=285)
    Button(form, text="Clear", command=clear_fields, width=8).place(x=245, y=285)

    Button(window, text="Back", command=back_command, width=10).place(x=45, y=450)
    refresh_room_list()
