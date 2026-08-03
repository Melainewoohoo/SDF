import json
from tkinter import *

try: 
    with open("studentStaff.json", "r") as file:
        data = json.load(file)
              
except FileNotFoundError:
        print("File not found")
        
except json.JSONDecodeError:
        print("Json file corrupted")
       

def student_login():
    window1 = Toplevel(window)
    window1.geometry("500x350")
    window1.title("Student Login")
    
    Label(window1, text="Login", font=("Calibri", 14)).pack()
    Label(window1, text="").pack()

    Label(window1, text="ID:").pack()
    Entry(window1, textvariable = id).pack()
    Label(window1, text="").pack()
    Label(window1, text="Password:").pack()
    #Entry(window1, textvariable = password, show="*").pack()
    Button(window1, text="Login").pack()
    Button(window1, text="Back").pack()

def staff_login():
    Label(text="Staff Login", font=("Calibri", 14)).pack()

def main_menu():
    global window   #to access another function
    window = Tk()   #create a window
    window.geometry("500x350")
    window.title("AMT Reservation System")
    Label(text="AMT Reservation System", font=("Calibri", 14)).pack()   #create text
    Label(text="").pack()       #new line
    Button(text= "Student Login", width="40", height="2", command=student_login).pack()
    Label(text="").pack()
    Button(text="Staff Login", width="40", height="2", command=staff_login).pack()
    window.mainloop()

main_menu()

def verify_user(ID, password):
    try: 
        with open("studentStaff.json", "r") as file:
            data = json.load(file)

        for student in data["students"]:
            if student["ID"] == ID and student["password"] == password:
                return True, student["Name"]

        return False, None      #No match found after checking all user

    except FileNotFoundError:
        print("File not found")
        return False, None
    except json.JSONDecodeError:
        print("Json file corrupted")
        return False, None




