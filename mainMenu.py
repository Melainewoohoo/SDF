import json
import os
from tkinter import *
from tkinter import messagebox
import facility_resource_management
import facility_usage_maintenance
from roomReservation import *

window = Tk()
window.geometry("925x500+300+200")
window.configure(bg="#fff")
window.title("AMT Reservation System")

try:
    with open("studentStaff.json") as file:
        data = json.load(file)

except FileNotFoundError:
    print("File not found")
    data = {"students": [], "staffs": []}

except json.JSONDecodeError:
    print("Json file corrupted")
    data = {"students": [], "staffs": []}


def base_layout(window):
     global img
     img = PhotoImage(file='login.png')
     Label(window, image=img, bg='white').place(x=50, y=50)

     frame = Frame(window, width=350, height=350, bg="white")
     frame.place(x=480, y=70)
     
     heading = Label(frame, text= "AMT Reservation System", fg="#57a1f8", 
               bg="white", font=("Microsoft YaHei UI Light", 14, "bold"))
     heading.place(x=85, y=5)

     return frame


def clear_window(window):
     for widget in window.winfo_children():
          widget.destroy()

def on_enter(e):
    e.widget.delete(0, 'end')

def verify_student(window):
    student_id = student.get()
    password = studPass.get()

    for student_data in data["students"]:
        if str(student_data["ID"]) == student_id and student_data["password"] == password:
            messagebox.showinfo("Login Successful", "Welcome, {}! :D".format(student_data["Name"]))
            student_menu(window, student_data)
            return

    messagebox.showerror("Login Failed", "Incorrect Student ID or Password.")


def student_menu(window, student_data):
    clear_window(window)
    window.title("Student Menu")

    frame = base_layout(window)
    Label(frame, text="Welcome, {}".format(student_data["Name"]), fg="#57a1f8",
          bg="white", font=("Microsoft YaHei UI Light", 12, "bold")).place(x=30, y=60)
    Button(frame, text="Reserve Room", font=("Microsoft YaHei UI Light", 11),
           command=lambda: None).place(x=30, y=110)
    Button(frame, text="Logout", font=("Microsoft YaHei UI Light", 11),
           command=lambda: main_menu(window)).place(x=30, y=150)

# ---------------------------------------------------------------------
# STUDENT LOGIN
# ---------------------------------------------------------------------
     
def student_login(window):
    global student, studPass
    clear_window(window)
    window.title("Student Login")

    frame = base_layout(window)

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

    Button(frame, text="Login", command=lambda: verify_student(window)).place(x=30, y=200)
    
    # Just close this Toplevel — the main menu window is already open behind it
    Button(frame, text="Back", command=lambda: main_menu(window)).place(x=100, y=200)

def staff_login(window):
    global staff, staffPass
    clear_window(window)
    window.title("Staff Login")

    frame = base_layout(window)

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

    Button(frame, text="Login", command=lambda: verify_staff(window)).place(x=30, y=200)
    Button(frame, text="Back", command=lambda: main_menu(window)).place(x=100, y=200)



def verify_staff(window):
    staff_id = staff.get()
    password = staffPass.get()

    for staff_data in data["staffs"]:
        if str(staff_data["ID"]) == staff_id and staff_data["password"] == password:
            messagebox.showinfo("Login Successful", "Welcome, {}! :D".format(staff_data["Name"]))
            staff_menu(window, staff_data)
            return

    messagebox.showerror("Login Failed", "Incorrect Staff ID or Password.")


def staff_menu(window, staff_data):
    clear_window(window)
    window.title("Staff Menu")

    frame = base_layout(window)

    Label(frame, text="Welcome, {}".format(staff_data["Name"]), fg="#57a1f8",
          bg="white", font=("Microsoft YaHei UI Light", 12, "bold")).place(x=30, y=60)

    Button(frame, text="Reserve Room", font=("Microsoft YaHei UI Light", 11),
           command=lambda: None).place(x=30, y=110)
    Button(frame, text="Facility Resource", font=("Microsoft YaHei UI Light", 11),
          command=lambda: facility_resource_management.FacilityResourceManagementFrame(window)).place(x=30, y=150)
    Button(frame, text="Facility Usage & Maintenance", font=("Microsoft YaHei UI Light", 11),
           command=lambda: facility_usage_maintenance.main(window)).place(x=30, y=190)

    Button(frame, text="Logout", font=("Microsoft YaHei UI Light", 11),
           command=lambda: main_menu(window)).place(x=30, y=230)


# ---------------------------------------------------------------------
# MAIN MENU
# ---------------------------------------------------------------------

def main_menu(window):
    # NOTE: this no longer creates a new Tk() each time — it just clears
    # and rebuilds the ONE window created at the bottom of this file.
    clear_window(window)
    window.title("AMT Reservation System")

    frame = base_layout(window)

    studentLoginButton = Button(frame, text="Student Login", command=lambda:student_login(window),
                                font=("Microsoft YaHei UI Light", 11))
    studentLoginButton.place(x=30, y=80)

    staffLoginButton = Button(frame, text="Staff Login", command=lambda:staff_login(window),
                              font=("Microsoft YaHei UI Light", 11))
    staffLoginButton.place(x=30, y=150)

main_menu(window)    
window.mainloop()   

