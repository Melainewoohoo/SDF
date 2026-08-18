import json
import os
from tkinter import *
from tkinter import messagebox
from roomReservation import *

try: 
    with open("studentStaff.json") as file:
        data = json.load(file)
              
except FileNotFoundError:
        print("File not found")
        
except json.JSONDecodeError:
        print("Json file corrupted")

def base_layout():
     global img
     img = PhotoImage(file='login.png')
     Label(window, image=img, bg='white').place(x=50, y=50)
     
     frame = Frame(window, width=350, height=350, bg="white")
     frame.place(x=480, y=70)
     
     heading = Label(frame, text= "AMT Reservation System", fg="#57a1f8", 
               bg="white", font=("Microsoft YaHei UI Light", 14, "bold"))
     heading.place(x=85, y=5)

     return frame

def clear_window():
     for widget in window.winfo_children():
          widget.destroy()

def on_enter(e):
     student.delete(0, 'end')

def verify_student():
    student_id = student.get()
    password = studPass.get()

    for student_data in data["students"]:
     if (str(student_data["ID"])== student_id and student_data["password"] == password):
          messagebox.showinfo("Login Successful", f"Welcome, {student_data["Name"]}! :D")

          return
     
def student_login():
    global student, studPass
    clear_window()
    window.title("Student Login")

    frame = base_layout()

    student = Entry(frame, width=25, fg="black", border=0, bg="white",
                        font= ("Microsoft YaHei UI Light",11))
    student.place(x=30, y=80)
    student.insert(0,"Student ID")
    student.bind('<FocusIn>', on_enter)
     
    Frame(frame, width=295, height=2, bg="black").place(x=25, y=107)
    
    studPass = Entry(frame, width=25, fg="black", border=0, bg="white",
                        font= ("Microsoft YaHei UI Light",11))
    studPass.place(x=30, y=150)
    studPass.insert(0,"Password")
    studPass.bind('<FocusIn>', on_enter)
    
    Frame(frame, width=295, height=2, bg="black").place(x=25, y=177)

    Button(window, text="Login", command=verify_student).place(x=35, y=187)
    Button(window, text="Reserve Room").pack()
    # Just close this Toplevel — the main menu window is already open behind it
    Button(window, text="     Back   ", command=main_menu).place(x=45, y=197)


def staff_login():
    clear_window()
    window.title("Staff Login")

    frame = base_layout()

    staff = Entry(frame, width=25, fg="black", border=0, bg="white",
                            font= ("Microsoft YaHei UI Light",11))
    staff.place(x=30, y=80)
    staff.insert(0,"Staff ID")
        
    Frame(frame, width=295, height=2, bg="black").place(x=25, y=107)
        
    staffPass = Entry(frame, width=25, fg="black", border=0, bg="white",
                            font= ("Microsoft YaHei UI Light",11))
    staffPass.place(x=30, y=150)
    staffPass.insert(0,"Password")
        
    Frame(frame, width=295, height=2, bg="black").place(x=25, y=177)

    Button(window, text="  Reserve Room  ").pack()
    Button(window, text="  Facility Resource  ").pack()
    Button(window, text="  Facility Usage & Maintenance  ").pack()
    Button(window, text="  Back  ", command=main_menu).place()


def main_menu():
    global window   # keep img referenced globally so it isn't garbage-collected
    window = Tk()
    window.geometry("925x500+300+200")
    window.configure(bg="#fff")
    window.title("AMT Reservation System")

    frame = base_layout()

    studentLoginButton = Button(frame, text="Student Login", command=student_login,
                                font=("Microsoft YaHei UI Light", 11))
    studentLoginButton.place(x=30, y=80)

    staffLoginButton = Button(frame, text="Staff Login", command=staff_login,
                              font=("Microsoft YaHei UI Light", 11))
    staffLoginButton.place(x=30, y=150)

    
main_menu()
window.mainloop()