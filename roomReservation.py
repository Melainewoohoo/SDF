import os
from tkinter import *

def booking_page(window):
    window.title("Facility Booking")
    
    booking_options = [
     "Discussion Room",
     "Lecture Hall",
     "Computer Laboratory",
     "Gymnasium",
     "Basketball Court",
     "Badminton Court",
     "Futsal",
     "Swimming Pool",
     "Track"
     ]
    
    clicked = StringVar()
    clicked.set(booking_options[0])
    drop = OptionMenu(window, clicked, *booking_options)
    drop.pack()
    bookingButton = Button(window, text="Show Selection").pack()
    myLabel = Label(window, text=clicked.get()).pack()
     








