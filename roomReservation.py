import json
import os
from tkinter import *

try: 
    with open("studentStaff.json") as file:
        data = json.load(file)
              
except FileNotFoundError:
        print("File not found")
        
except json.JSONDecodeError:
        print("Json file corrupted")

# temp_id = list(data["ID"])
# temp_password = list(data["password"])

# id = temp_id
# password = temp_password


def verify_user(id, password):
   
    for student in data["students"]:
            if student["ID"] == id and student["password"] == password:
                return True, student["Name"]

            return False, None      #No match found after checking all user
     

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
     








