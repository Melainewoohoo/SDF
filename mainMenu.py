import json
import os
from tkinter import *

def student_login():
    window1 = Toplevel(window)
    window1.geometry("925x500+300+200")
    window1.configure(bg="#fff")
    window1.title("Main Menu")

    frame = Frame(window1, width=350, height=350, bg="white")
    frame.place(x=480, y=70)

    heading = Label(frame, text="MainMenu", fg="#57a1f8",
                    bg="white", font=("Microsoft YaHei UI Light", 14, "bold"))
    heading.place(x=85, y=5)

    Button(window1, text="Reserve Room").pack()
    # Just close this Toplevel — the main menu window is already open behind it
    Button(window1, text="     Back   ", command=window1.destroy).pack()


def staff_login():
    window2 = Toplevel(window)
    window2.geometry("925x500+300+200")
    window2.configure(bg="#fff")
    window2.title("Main Menu")

    frame = Frame(window2, width=350, height=350, bg="white")
    frame.place(x=480, y=70)

    heading = Label(frame, text="Main Menu", fg="#57a1f8",
                    bg="white", font=("Microsoft YaHei UI Light", 14, "bold"))
    heading.place(x=85, y=5)

    staff = Entry(frame, width=25, fg="black", border=0, bg="white",
                        font=("Microsoft YaHei UI Light", 11))

    Button(window2, text="  Reserve Room  ").pack()
    Button(window2, text="  Facility Resource  ").pack()
    Button(window2, text="  Facility Usage & Maintenance  ").pack()
    Button(window2, text="  Back  ", command=window2.destroy).pack()


def main_menu():
    global window, img   # keep img referenced globally so it isn't garbage-collected
    window = Tk()
    window.geometry("925x500+300+200")
    window.configure(bg="#fff")
    window.title("AMT Reservation System")

    img = PhotoImage(file='login.png')
    Label(window, image=img, bg='white').place(x=50, y=50)

    frame = Frame(window, width=350, height=350, bg="white")
    frame.place(x=480, y=70)

    heading = Label(frame, text="AMT Reservation System", fg="#57a1f8",
                    bg="white", font=("Microsoft YaHei UI Light", 14, "bold"))
    heading.place(x=85, y=5)

    studentLoginButton = Button(frame, text="Student Login", command=student_login,
                                font=("Microsoft YaHei UI Light", 11))
    studentLoginButton.place(x=30, y=80)

    staffLoginButton = Button(frame, text="Staff Login", command=staff_login,
                              font=("Microsoft YaHei UI Light", 11))
    staffLoginButton.place(x=30, y=150)

    window.mainloop()

main_menu()