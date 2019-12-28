
#!/user/bin/env python3
# -*- coding: utf-8 -*-

"""
    need to install java, pandas, numpy,lxml
    __author__ = 'Cammie Zhao'
    __author_email__ = "jie.zhao_1@nxp.com"
https://tabula.technology/
"""

import tkinter as tk
import tkinter.messagebox
import pickle
window = tk.Tk()
window.title('welcome to python')
window.geometry('500x400')

canvas=tk.Canvas(window,height=140,width=480)
image_file=tk.PhotoImage(file='welcome.gif')
image=canvas.create_image(30,10,anchor='nw',image=image_file)
canvas.pack(side='top')

tk.Label(window,text='user name:',height=2,width=10).place(x=140,y=150,anchor='nw')
var_usr_name=tk.StringVar()
tk.Entry(window,textvariable=var_usr_name).place(x=230,y=160,anchor='nw')

tk.Label(window,text='password:',height=2,width=10).place(x=140,y=180,anchor='nw')
var_usr_pwd=tk.StringVar()
tk.Entry(window,textvariable=var_usr_pwd).place(x=230,y=190,anchor='nw')

def Login():
    usr_name=var_usr_name.get()
    usr_pwd=var_usr_pwd.get()
    try:
        with open('usr_info.pickle','rb')as usr_file:
            usr_info=pickle.load(usr_file)
    except FileNotFoundError:
        with open('usr_info.pickle','wb')as usr_file:
            usr_info={'admin':'admin'}
            pickle.dump(usr_info,usr_file)
    if usr_name in usr_info:
        if usr_pwd==usr_info[usr_name]:
            tk.messagebox.showinfo(title='welcome',message='How are you ?')
        else:
            tk.messagebox.showerror(title='error',message='Your password is wrong!')
    else:
        is_sign_up=tk.messagebox.showinfo(title='hint',message='please sign up first!')
        if is_sign_up:
            sign_up()

def sign_up():
    def save_info():
        p=sign_up_password.get()
        pf=sign_up_password2.get()
        n=sign_up_name.get()
        with open('usr_info.pickle','rb') as usr_file:
            exist_usr_info=pickle.load(usr_file)
        if p!=pf:
            tk.messagebox.showerror(title='Error',message='The password should be same!')
        elif n in exist_usr_info:
            tk.messagebox.showwarning(title='Error',message='The user has already ')
        else:
            exist_usr_info[n]=p
            with open('usr_info.pickle','wb') as usr_file:
                pickle.dump(exist_usr_info,usr_file)
            tk.messagebox.showinfo(title='Welcome',message='You have successfully signed up!')
            window_sign_up.destroy()
    window_sign_up=tk.Toplevel(window)
    window_sign_up.geometry('350x200')
    window_sign_up.title('Sign up window')
    tk.Label(window_sign_up,text='user name:').place(x=50,y=30)
    sign_up_name=tk.StringVar()
    tk.Entry(window_sign_up,textvariable=sign_up_name).place(x=160,y=35)
    tk.Label(window_sign_up,text='Entry password:').place(x=50,y=60)
    sign_up_password=tk.StringVar()
    tk.Entry(window_sign_up,textvariable=sign_up_password).place(x=160,y=65)
    tk.Label(window_sign_up, text='Confirm password:').place(x=50, y=90)
    sign_up_password2 = tk.StringVar()
    tk.Entry(window_sign_up, textvariable=sign_up_password2).place(x=160, y=95)
    tk.Button(window_sign_up,text='Sign up',command=save_info).place(x=160,y=125)


tk.Button(window,text='Login',command=Login).place(x=240,y=230,anchor='nw')
tk.Button(window,text='Sign up',command=sign_up).place(x=300,y=230,anchor='nw')

window.mainloop()

