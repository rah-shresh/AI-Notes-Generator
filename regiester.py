from tkinter import *
from tkinter import messagebox
from db_connection import connect_db

root = Tk()
root.title("Registration Form")
root.geometry("450x500")

Label(root, text="Registration Form", font=("Arial",18,"bold")).pack(pady=10)

Label(root, text="Name").pack()
name = Entry(root, width=35)
name.pack()

Label(root, text="Email").pack()
email = Entry(root, width=35)
email.pack()

Label(root, text="Mobile").pack()
mobile = Entry(root, width=35)
mobile.pack()

Label(root, text="Password").pack()
password = Entry(root, show="*", width=35)
password.pack()

def register():

    if name.get()=="" or email.get()=="" or mobile.get()=="" or password.get()=="":
        messagebox.showerror("Error","All fields are required")
        return

    try:

        con = connect_db()
        cur = con.cursor()

        sql = """
        INSERT INTO users(name,email,mobile,password)
        VALUES(%s,%s,%s,%s)
        """

        values = (
            name.get(),
            email.get(),
            mobile.get(),
            password.get()
        )

        cur.execute(sql, values)

        con.commit()

        messagebox.showinfo("Success","Registration Successful")

        name.delete(0,END)
        email.delete(0,END)
        mobile.delete(0,END)
        password.delete(0,END)

        con.close()

    except Exception as e:
        messagebox.showerror("Database Error ",str(e))

Button(
    root,
    text="Register",
    command=register,
    bg="green",
    fg="white",
    width=20
).pack(pady=20)

root.mainloop()