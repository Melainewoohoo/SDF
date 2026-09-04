import json
import os
from tkinter import *
from tkinter import messagebox
import facility_resource_management
import facility_usage_maintenance
from roomReservation import *

try:
    with open("studentStaff.json") as file:
        data = json.load(file)

except FileNotFoundError:
    print("File not found")
    data = {"students": [], "staffs": []}

except json.JSONDecodeError:
    print("Json file corrupted")
    data = {"students": [], "staffs": []}


def base_layout():
    global img
    img = PhotoImage(file='login2.png')
    Label(window, image=img, bg='white').place(x=50, y=50)

    frame = Frame(window, width=350, height=350, bg="white")
    frame.place(x=480, y=70)

    heading = Label(frame, text="AMT Reservation System", fg="#57a1f8",
                     bg="white", font=("Microsoft YaHei UI Light", 14, "bold"))
    heading.place(x=85, y=5)

    return frame


def clear_window():
    for widget in window.winfo_children():
        widget.destroy()

def on_enter(e):
    # Clears the placeholder text in whichever Entry was just focused
    e.widget.delete(0, 'end')

def open_facility_resource_management(staff_data):
    clear_window()
    window.title("Facility Resource Management")
    window.geometry("1280x650")

    Button(window, text="Back", command=lambda: staff_menu(staff_data),
           font=("Microsoft YaHei UI Light", 10), width=10).pack(
               anchor="w", padx=10, pady=(10, 0)
           )

    page = facility_resource_management.FacilityResourceManagementFrame(window)
    page.pack(fill="both", expand=True)

def open_facility_usage_maintenance(staff_data):
    clear_window()
    window.title("Facility Usage & Maintenance Management")
    window.geometry("1280x650")

    page = facility_usage_maintenance.FacilityUsageMaintenanceFrame(window, back_command=lambda: staff_menu(staff_data))
    page.pack(fill="both", expand=True)


# ---------------------------------------------------------------------
# STUDENT LOGIN
# ---------------------------------------------------------------------

def student_login():
    global student, studPass
    clear_window()
    window.title("Student Login")

    frame = base_layout()

    student = Entry(frame, width=25, fg="black", border=0, bg="white",
                     font=("Microsoft YaHei UI Light", 11))
    student.place(x=30, y=80)
    student.insert(0, "Student ID")
    student.bind('<FocusIn>', on_enter)

    Frame(frame, width=295, height=2, bg="black").place(x=25, y=107)

    studPass = Entry(frame, width=25, fg="black", border=0, bg="white",
                      font=("Microsoft YaHei UI Light", 11), show="*")
    studPass.place(x=30, y=150)
    studPass.insert(0, "Password")
    studPass.bind('<FocusIn>', on_enter)

    Frame(frame, width=295, height=2, bg="black").place(x=25, y=177)

    Button(frame, text="Login", command=verify_student).place(x=30, y=200)
    Button(frame, text="Back", command=main_menu).place(x=100, y=200)


def verify_student():
    student_id = student.get()
    password = studPass.get()

    for student_data in data["students"]:
        if str(student_data["ID"]) == student_id and student_data["password"] == password:
            messagebox.showinfo("Login Successful", "Welcome, {}! :D".format(student_data["Name"]))
            student_menu(student_data)
            return

    messagebox.showerror("Login Failed", "Incorrect Student ID or Password.")


def student_menu(student_data):
    clear_window()
    window.title("Student Menu")
    window.geometry("925x500+300+200")
    frame = base_layout()

    Label(frame, text="Welcome, {}".format(student_data["Name"]), fg="#57a1f8",
          bg="white", font=("Microsoft YaHei UI Light", 12, "bold")).place(x=30, y=60)

    Button(frame, text="Reserve Venue", font=("Microsoft YaHei UI Light", 11),
           command=lambda: booking_page(
               window, student_data, lambda: student_menu(student_data)
           )).place(x=30, y=110)

    Button(frame, text="My Booking", font=("Microsoft YaHei UI Light", 11),
           command=lambda: booking_history_page(
               window, student_data, lambda: student_menu(student_data)
           )).place(x=30, y=150)

    Button(frame, text="Logout", font=("Microsoft YaHei UI Light", 11),
           command=main_menu).place(x=30, y=190)


# ---------------------------------------------------------------------
# STAFF LOGIN
# ---------------------------------------------------------------------

def staff_login():
    global staff, staffPass
    clear_window()
    window.title("Staff Login")

    frame = base_layout()

    staff = Entry(frame, width=25, fg="black", border=0, bg="white",
                  font=("Microsoft YaHei UI Light", 11))
    staff.place(x=30, y=80)
    staff.insert(0, "Staff ID")
    staff.bind('<FocusIn>', on_enter)

    Frame(frame, width=295, height=2, bg="black").place(x=25, y=107)

    staffPass = Entry(frame, width=25, fg="black", border=0, bg="white",
                       font=("Microsoft YaHei UI Light", 11), show="*")
    staffPass.place(x=30, y=150)
    staffPass.insert(0, "Password")
    staffPass.bind('<FocusIn>', on_enter)

    Frame(frame, width=295, height=2, bg="black").place(x=25, y=177)

    Button(frame, text="Login", command=verify_staff).place(x=30, y=200)
    Button(frame, text="Back", command=main_menu).place(x=100, y=200)


def verify_staff():
    staff_id = staff.get()
    password = staffPass.get()

    for staff_data in data["staffs"]:
        if str(staff_data["ID"]) == staff_id and staff_data["password"] == password:
            messagebox.showinfo("Login Successful", "Welcome, {}! :D".format(staff_data["Name"]))
            staff_menu(staff_data)
            return

    messagebox.showerror("Login Failed", "Incorrect Staff ID or Password.")


def staff_menu(staff_data):
    clear_window()
    window.title("Staff Menu")
    window.geometry("925x500+300+200")

    frame = base_layout()

    Label(frame, text="Welcome, {}".format(staff_data["Name"]), fg="#57a1f8",
          bg="white", font=("Microsoft YaHei UI Light", 12, "bold")).place(x=30, y=60)

    Button(frame, text="Facility Resource management", font=("Microsoft YaHei UI Light", 11),
          command=lambda: open_facility_resource_management(staff_data)).place(x=30, y=110)
    Button(frame, text="Facility Usage & Maintenance", font=("Microsoft YaHei UI Light", 11),
          command=lambda: open_facility_usage_maintenance(staff_data)).place(x=30, y=150)
    Button(frame, text="Logout", font=("Microsoft YaHei UI Light", 11),
           command=main_menu).place(x=30, y=230)

# MAIN MENU
def main_menu():
    # NOTE: this no longer creates a new Tk() each time — it just clears
    # and rebuilds the ONE window created at the bottom of this file.
    clear_window()
    window.title("AMT Reservation System")
    window.geometry("925x500+300+200")
    frame = base_layout()

    studentLoginButton = Button(frame, text="Student Login", command=student_login,
                                 font=("Microsoft YaHei UI Light", 11))
    studentLoginButton.place(x=30, y=80)

    staffLoginButton = Button(frame, text="Staff Login", command=staff_login,
                               font=("Microsoft YaHei UI Light", 11))
    staffLoginButton.place(x=30, y=150)


# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------

window = Tk()
window.geometry("925x500+300+200")
window.configure(bg="#fff")
window.title("AMT Reservation System")

main_menu()
window.mainloop()
