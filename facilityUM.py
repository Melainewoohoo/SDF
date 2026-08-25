import json
import os
from tkinter import *

# def Add_facility():
#     window1 = Toplevel(window)
#     window1.geometry("925x500+300+200")
#     window1.configure(bg="#fff")
#     window1.title("Add Facility")

#     frame = Frame(window1, width=450, height=350, bg="white")
#     frame.place(x=400, y=70)

#     heading = Label(frame, text="Add Facility", fg="#57a1f8",
#                      bg="white", font=("Microsoft YaHei UI Light", 14, "bold"),
#                      wraplength=430, justify="center")
#     heading.place(x=10, y=5, width=430)

#     Button(window1, text="     Back   ", command=window1.destroy).pack()

def Update_facility():
    window1 = Toplevel(window)
    window1.geometry("925x500+300+200")
    window1.configure(bg="#fff")
    window1.title("Update Facility")

    frame = Frame(window1, width=450, height=350, bg="white")
    frame.place(x=400, y=70)

    heading = Label(frame, text="Update Facility", fg="#57a1f8",
                     bg="white", font=("Microsoft YaHei UI Light", 14, "bold"),
                     wraplength=430, justify="center")
    heading.place(x=10, y=5, width=430)

    Button(window1, text="     Back   ", command=window1.destroy).pack()


# def Remove_facility():
#     window2 = Toplevel(window)
#     window2.geometry("925x500+300+200")
#     window2.configure(bg="#fff")
#     window2.title("Remove Facility")

#     frame = Frame(window2, width=450, height=350, bg="white")
#     frame.place(x=400, y=70)

#     heading = Label(frame, text="Remove Facility", fg="#57a1f8",
#                      bg="white", font=("Microsoft YaHei UI Light", 14, "bold"),
#                      wraplength=430, justify="center")
#     heading.place(x=10, y=5, width=430)

#     staff = Entry(frame, width=25, fg="black", border=0, bg="white",
#                   font=("Microsoft YaHei UI Light", 11))

#     Button(window2, text="  Back  ", command=window2.destroy).pack()


def facilityUM(parent):
    global window
    window = Toplevel(parent)
    window.geometry("925x500+300+200")
    window.configure(bg="#fff")
    window.title("Facility Usage and Maintenance")

    frame = Frame(window, width=450, height=350, bg="white")
    frame.place(x=400, y=70)

    heading = Label(frame, text="Facility Usage and Maintenance", fg="#57a1f8",
                     bg="white", font=("Microsoft YaHei UI Light", 14, "bold"),
                     wraplength=430, justify="center")
    heading.place(x=10, y=5, width=430)

    # AddFacilityButton = Button(frame, text= "Add Facility", command=Add_facility, 
    #                                 font=("Microsoft YaHei UI Light", 11))
    # AddFacilityButton.place(x=30, y=80)

    # RemoveFacilityButton = Button(frame, text= "Remove Facility", command=Remove_facility, 
    #                                 font=("Microsoft YaHei UI Light", 11))
    # RemoveFacilityButton.place(x=30, y=120)

    UpdateFacilityButton = Button(frame, text= "Update Facility", command=Update_facility, 
                                    font=("Microsoft YaHei UI Light", 11))
    UpdateFacilityButton.place(x=30, y=160)

    GoBack = Button(window, text="     Back   ", command=window.destroy,
                     font=("Microsoft YaHei UI Light", 11))
    GoBack.place(x=60, y=170)
