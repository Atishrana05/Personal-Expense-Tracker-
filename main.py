#!/usr/bin/env python3
"""
Personal Expense Tracker (Multi-user)
Run: python main.py
Requirements: matplotlib
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import hashlib
from datetime import datetime
import csv
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

DB_FILE = 'expenses.db'

# ---------------------- Database Setup ----------------------
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# ---------------------- Utilities ----------------------
def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

# ---------------------- App ----------------------
class ExpenseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Expense Tracker')
        self.geometry('900x600')
        self.minsize(820, 520)
        # ttk style for modern-ish look
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        self.current_user = None  # will be (id, username)
        # main container
        self.container = ttk.Frame(self)
        self.container.pack(fill='both', expand=True)

        # frames
        self.frames = {}
        for F in (LoginFrame, RegisterFrame, DashboardFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky='nsew')

        self.show_frame('LoginFrame')

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()

    def login_user(self, user_id, username):
        self.current_user = (user_id, username)
        self.frames['DashboardFrame'].refresh_user()
        self.show_frame('DashboardFrame')

    def logout(self):
        self.current_user = None
        self.show_frame('LoginFrame')

# ---------------------- Login Frame ----------------------
class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller: ExpenseApp):
        super().__init__(parent)
        self.controller = controller

        # left: brand
        left = ttk.Frame(self, padding=20)
        left.pack(side='left', fill='y')
        brand = ttk.Label(left, text='Expense Tracker', font=('Inter', 22, 'bold'))
        brand.pack(pady=(40, 10))
        sub = ttk.Label(left, text='Securely manage your expenses', font=('Inter', 10))
        sub.pack(pady=(0, 20))

        # right: login card
        right = ttk.Frame(self, padding=30)
        right.pack(side='left', fill='both', expand=True)

        card = ttk.LabelFrame(right, text='Login', padding=20)
        card.pack(anchor='center', pady=60, ipadx=20, ipady=10)

        ttk.Label(card, text='Username').grid(row=0, column=0, sticky='w')
        self.username_entry = ttk.Entry(card, width=30)
        self.username_entry.grid(row=0, column=1, pady=6)

        ttk.Label(card, text='Password').grid(row=1, column=0, sticky='w')
        self.password_entry = ttk.Entry(card, show='*', width=30)
        self.password_entry.grid(row=1, column=1, pady=6)

        login_btn = ttk.Button(card, text='Login', command=self.handle_login)
        login_btn.grid(row=2, column=0, columnspan=2, pady=(12, 6), sticky='we')

        reg_btn = ttk.Button(card, text='Register', command=lambda: controller.show_frame('RegisterFrame'))
        reg_btn.grid(row=3, column=0, columnspan=2, sticky='we')

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning('Missing', 'Please enter username and password')
            return
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
        conn.close()
        if not row:
            messagebox.showerror('No user', 'User not found. Please register first.')
            return
        if hash_password(password) == row['password_hash']:
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.controller.login_user(row['id'], username)
        else:
            messagebox.showerror('Invalid', 'Wrong password')

# ---------------------- Register Frame ----------------------
class RegisterFrame(ttk.Frame):
    def __init__(self, parent, controller: ExpenseApp):
        super().__init__(parent)
        self.controller = controller

        frame = ttk.Frame(self, padding=30)
        frame.pack(fill='both', expand=True)

        card = ttk.LabelFrame(frame, text='Create Account', padding=20)
        card.pack(pady=60)

        ttk.Label(card, text='Username').grid(row=0, column=0, sticky='w')
        self.username_entry = ttk.Entry(card, width=30)
        self.username_entry.grid(row=0, column=1, pady=6)

        ttk.Label(card, text='Password').grid(row=1, column=0, sticky='w')
        self.password_entry = ttk.Entry(card, show='*', width=30)
        self.password_entry.grid(row=1, column=1, pady=6)

        ttk.Label(card, text='Confirm').grid(row=2, column=0, sticky='w')
        self.confirm_entry = ttk.Entry(card, show='*', width=30)
        self.confirm_entry.grid(row=2, column=1, pady=6)

        register_btn = ttk.Button(card, text='Register', command=self.handle_register)
        register_btn.grid(row=3, column=0, columnspan=2, pady=(10, 6), sticky='we')

        back_btn = ttk.Button(card, text='Back to Login', command=lambda: controller.show_frame('LoginFrame'))
        back_btn.grid(row=4, column=0, columnspan=2, sticky='we')

    def handle_register(self):
        username = self.username_entry.get().strip()
        pw = self.password_entry.get().strip()
        conf = self.confirm_entry.get().strip()
        if not username or not pw or not conf:
            messagebox.showwarning('Missing', 'Fill all fields')
            return
        if pw != conf:
            messagebox.showerror('Mismatch', 'Passwords do not match')
            return
        pw_hash = hash_password(pw)
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, password_hash, created_at) VALUES (?,?,?)',
                        (username, pw_hash, datetime.now().isoformat()))
            conn.commit()
            messagebox.showinfo('Success', 'Account created. Please login.')
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.confirm_entry.delete(0, tk.END)
            self.controller.show_frame('LoginFrame')
        except sqlite3.IntegrityError:
            messagebox.showerror('Exists', 'Username already exists')
        finally:
            conn.close()

# ---------------------- Dashboard Frame ----------------------
class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller: ExpenseApp):
        super().__init__(parent)
        self.controller = controller

        topbar = ttk.Frame(self, padding=(10, 8))
        topbar.pack(fill='x')
        self.user_label = ttk.Label(topbar, text='')
        self.user_label.pack(side='left')

        logout_btn = ttk.Button(topbar, text='Logout', command=self.controller.logout)
        logout_btn.pack(side='right')

        # main content split
        content = ttk.PanedWindow(self, orient='horizontal')
        content.pack(fill='both', expand=True, padx=10, pady=10)

        # left panel - add expense
        left = ttk.Frame(content, width=320)
        content.add(left, weight=1)

        card = ttk.LabelFrame(left, text='Add Expense', padding=12)
        card.pack(fill='x', padx=6, pady=6)

        ttk.Label(card, text='Amount').grid(row=0, column=0, sticky='w')
        self.amount_entry = ttk.Entry(card)
        self.amount_entry.grid(row=0, column=1, pady=6)

        ttk.Label(card, text='Category').grid(row=1, column=0, sticky='w')
        self.category_cb = ttk.Combobox(card, values=['Food', 'Travel', 'Groceries', 'Bills', 'Entertainment', 'Other'])
        self.category_cb.grid(row=1, column=1, pady=6)
        self.category_cb.set('Food')

        ttk.Label(card, text='Note').grid(row=2, column=0, sticky='w')
        self.note_entry = ttk.Entry(card)
        self.note_entry.grid(row=2, column=1, pady=6)

        add_btn = ttk.Button(card, text='Add', command=self.add_expense)
        add_btn.grid(row=3, column=0, columnspan=2, sticky='we', pady=(8, 0))

        # export and chart buttons
        tools = ttk.Frame(left, padding=6)
        tools.pack(fill='x', padx=6, pady=6)
        exp_btn = ttk.Button(tools, text='Export CSV', command=self.export_csv)
        exp_btn.pack(side='left', padx=(0,6))
        chart_btn = ttk.Button(tools, text='Show Charts', command=self.show_charts)
        chart_btn.pack(side='left')

        # right panel - table
        right = ttk.Frame(content)
        content.add(right, weight=3)

        searchbar = ttk.Frame(right)
        searchbar.pack(fill='x', pady=(0,8))
        ttk.Label(searchbar, text='Search').pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(searchbar, textvariable=self.search_var)
        search_entry.pack(side='left', padx=(6,6))
        search_entry.bind('<KeyRelease>', lambda e: self.refresh_table())

        self.tree = ttk.Treeview(right, columns=('id','amount','category','note','date'), show='headings')
        for col, w in [('id',40), ('amount',90), ('category',120), ('note',260), ('date',150)]:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=w, anchor='center')
        self.tree.pack(fill='both', expand=True)

        # delete button
        del_btn = ttk.Button(right, text='Delete Selected', command=self.delete_selected)
        del_btn.pack(pady=6)

    def refresh_user(self):
        uid, uname = self.controller.current_user
        self.user_label.config(text=f'Logged in as: {uname}')
        self.refresh_table()

    def add_expense(self):
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror('Invalid', 'Enter a valid amount')
            return
        category = self.category_cb.get().strip() or 'Other'
        note = self.note_entry.get().strip()
        date = datetime.now().isoformat()
        uid, _ = self.controller.current_user
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO expenses (user_id, amount, category, note, date) VALUES (?,?,?,?,?)',
                    (uid, amount, category, note, date))
        conn.commit()
        conn.close()
        self.amount_entry.delete(0, tk.END)
        self.note_entry.delete(0, tk.END)
        messagebox.showinfo('Saved', 'Expense added')
        self.refresh_table()

    def refresh_table(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        uid, _ = self.controller.current_user
        q = 'SELECT id, amount, category, note, date FROM expenses WHERE user_id = ? ORDER BY date DESC'
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(q, (uid,))
        rows = cur.fetchall()
        conn.close()
        term = self.search_var.get().lower().strip()
        for r in rows:
            if term:
                if term in str(r['amount']).lower() or term in r['category'].lower() or term in (r['note'] or '').lower() or term in r['date'].lower():
                    self.tree.insert('', tk.END, values=(r['id'], r['amount'], r['category'], r['note'], r['date']))
            else:
                self.tree.insert('', tk.END, values=(r['id'], r['amount'], r['category'], r['note'], r['date']))

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('None', 'Select a row to delete')
            return
        ids = [self.tree.item(s)['values'][0] for s in sel]
        if not messagebox.askyesno('Confirm', f'Delete {len(ids)} record(s)?'):
            return
        conn = get_db_connection()
        cur = conn.cursor()
        cur.executemany('DELETE FROM expenses WHERE id = ?', [(i,) for i in ids])
        conn.commit()
        conn.close()
        self.refresh_table()

    def export_csv(self):
        uid, uname = self.controller.current_user
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT amount, category, note, date FROM expenses WHERE user_id = ? ORDER BY date DESC', (uid,))
        rows = cur.fetchall()
        conn.close()
        if not rows:
            messagebox.showinfo('Empty', 'No records to export')
            return
        f = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files','*.csv')], initialfile=f'expenses_{uname}.csv')
        if not f:
            return
        with open(f, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Amount', 'Category', 'Note', 'Date'])
            for r in rows:
                writer.writerow([r['amount'], r['category'], r['note'], r['date']])
        messagebox.showinfo('Saved', f'Exported to {os.path.basename(f)}')

    def show_charts(self):
        uid, _ = self.controller.current_user
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category', (uid,))
        rows = cur.fetchall()
        conn.close()
        if not rows:
            messagebox.showinfo('No data', 'Add some expenses to see charts')
            return
        categories = [r['category'] for r in rows]
        totals = [r['total'] for r in rows]

        # create a new Toplevel window for charts
        win = tk.Toplevel(self)
        win.title('Spending Charts')
        win.geometry('700x500')

        nb = ttk.Notebook(win)
        nb.pack(fill='both', expand=True)

        # Pie chart tab
        f1 = ttk.Frame(nb)
        nb.add(f1, text='Pie Chart')
        fig1 = plt.Figure(figsize=(6,4), dpi=100)
        ax1 = fig1.add_subplot(111)
        ax1.pie(totals, labels=categories, autopct='%1.1f%%', startangle=140)
        ax1.axis('equal')
        canvas1 = FigureCanvasTkAgg(fig1, master=f1)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill='both', expand=True)

        # Bar chart tab
        f2 = ttk.Frame(nb)
        nb.add(f2, text='Bar Chart')
        fig2 = plt.Figure(figsize=(6,4), dpi=100)
        ax2 = fig2.add_subplot(111)
        ax2.bar(categories, totals)
        ax2.set_ylabel('Amount')
        ax2.set_title('Spending by Category')
        canvas2 = FigureCanvasTkAgg(fig2, master=f2)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill='both', expand=True)

# ---------------------- Main ----------------------
if __name__ == '__main__':
    init_db()
    app = ExpenseApp()
    app.mainloop()
