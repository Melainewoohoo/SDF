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
     
def student_login():
    window1 = Toplevel(window)
    window1.geometry("925x500+300+200")
    window1.configure(bg="#fff")
    window1.title("Student Login")

#-----------------------------------------Layout----------------------------------------
    img = PhotoImage(file='login.png')
    Label(window1, image=img, bg='white').place(x=50, y=50)

    frame = Frame(window1, width=350, height=350, bg="white")
    frame.place(x=480, y=70)

    heading = Label(frame, text= "AMT Reservation System", fg="#57a1f8", 
                    bg="white", font=("Microsoft YaHei UI Light", 14, "bold"))
    heading.place(x=85, y=5)

#--------------------------------------Student Login------------------------------------
    student = Entry(frame, width=25, fg="black", border=0, bg="white",
                    font= ("Microsoft YaHei UI Light",11))
    student.place(x=30, y=80)
    student.insert(0,"Student ID")

    Frame(frame, width=295, height=2, bg="black").place(x=25, y=107)

    studPass = Entry(frame, width=25, fg="black", border=0, bg="white",
                    font= ("Microsoft YaHei UI Light",11))
    studPass.place(x=30, y=150)
    studPass.insert(0,"Password")

    Frame(frame, width=295, height=2, bg="black").place(x=25, y=177)

    Button(window1, text="Login").pack()
    Button(window1, text="Back", command=main_menu).pack()

def staff_login():
    window2 = Toplevel(window)
    window2.geometry("925x500+300+200")
    window2.configure(bg="#fff")
    window2.title("Staff Login")

#-----------------------------------------Layout----------------------------------------
    img = PhotoImage(file='login.png')
    Label(window2, image=img, bg='white').place(x=50, y=50)

    frame = Frame(window2, width=350, height=350, bg="white")
    frame.place(x=480, y=70)

    heading = Label(frame, text= "AMT Reservation System", fg="#57a1f8", 
                    bg="white", font=("Microsoft YaHei UI Light", 14, "bold"))
    heading.place(x=85, y=5)

#--------------------------------------Staff Login--------------------------------------
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

def booking_page():
    window3 = Toplevel(window)
    window3.geometry("925x500+300+200")
    window3.configure(bg="#fff")
    heading = Label(text= "AMT Reservation System", fg="#57a1f8", 
                    bg="white", font=("Microsoft YaHei UI Light", 14, "bold"))
    heading.place(x=50, y=70)

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
    drop = OptionMenu(window3, clicked, *booking_options)
    drop.pack()
    bookingButton = Button(window3, text="Show Selection").pack()
    myLabel = Label(window3, text=clicked.get()).pack()

     

def main_menu():
    global window   #to access another function
    window = Tk()   #create a window
    window.geometry("925x500+300+200")
    window.configure(bg="#fff")
    window.title("AMT Reservation System")

#-----------------------------------------Layout----------------------------------------
    img = PhotoImage(file='login.png')
    Label(window, image=img, bg='white').place(x=50, y=50)

    frame = Frame(window, width=350, height=350, bg="white")
    frame.place(x=480, y=70)

    heading = Label(frame, text= "AMT Reservation System", fg="#57a1f8", 
                    bg="white", font=("Microsoft YaHei UI Light", 14, "bold"))
    heading.place(x=85, y=5)

#------------------------------------------Button---------------------------------------
    studentLoginButton = Button(frame, text= "Student Login", command=student_login, 
                                font=("Microsoft YaHei UI Light", 11))
    studentLoginButton.place(x=30, y=80)

    staffLoginButton = Button(frame, text= "Staff Login", command=staff_login, 
                              font=("Microsoft YaHei UI Light", 11))
    staffLoginButton.place(x=30, y=150)

#-----------------------------------------Testing---------------------------------------
    bookingButton = Button(frame, text= "Booking", command=booking_page, 
                                  font=("Microsoft YaHei UI Light", 11))
    bookingButton.place(x=30, y=200)

    window.mainloop()

main_menu()







