import json

from tkinter import *
window = Tk()   #create a window
lbl = Label(window, Text="Hello World")     #create label
lbl.pack(expand=True)
window.mainloop()


def verify_user(ID, password):
    try: 
        with open("Documents\Assignments\SDF\studentStaff.json", "r") as file:
            users = json.load(file)

        for user in users:
            if user["ID"] == ID and user["password"] == password:
                return True, user["Name"]

        return False, None      #No match found after checking all user

    except FileNotFoundError:
        print("File not found")
        return False, None
    except json.JSONDecodeError:
        print("Json file corrupted")
        return False, None

#---------------------------------------------------User Input---------------------------------------------      
user_id = int(input("Enter your ID uwu:"))
user_pw = input("Enter password:")

success, Name = verify_user(user_id, user_pw)

if success:
    print(f"Access Granted! Welcome {Name}! :D")
else:
    print("Access Denied: Invalid ID or Password")

