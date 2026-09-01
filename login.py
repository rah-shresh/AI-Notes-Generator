from tkinter import *
from tkinter import messagebox
from db_connection import connect_db

root=Tk()
root.title("Login Form")
root.geometry("400x300")
root.resizable(False,False)
Label(root,text="Login Form",font=("Arial",18,"bold")).pack(pady=15)

#label for email
Label(root,text="Email").pack()
email=Entry(root,width=35)
email.pack(pady=5)

Label(root,text="Password").pack()
password=Entry(root,show="*",width=35)
password.pack(pady=5)

def login():
    if email.get()=="" or password.get()=="":
        messagebox.showerror("error","All fields are required")
        return
    try:
        con=connect_db()
        cur=con.cursor()
        sql="""
             select * from users where email=%s AND password=%s
             """
        cur.execute(sql,(email.get(),password.get()))
        user=cur.fetchone()
        if user :
            messagebox.showinfo("success",f"welcome {user[1]}")
        else:
            messagebox.showerror("Login Failed","Invalid email or password")
    except Exception as e:
        messagebox.showerror("Database error ",str(e))
Button(root,text="Login",command=login,bg="blue",fg="white",width=20).pack(pady=20)

root.mainloop()