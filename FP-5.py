
import re
import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

DB_PATH = "customer_info.db"

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    birthday TEXT NOT NULL,        -- stored as ISO date string YYYY-MM-DD
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    preferred_contact TEXT NOT NULL CHECK (preferred_contact IN ('Email','Phone','Mail')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9\s\-\+\(\)]{7,}$")  # simple, flexible phone check


def init_db():
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute(TABLE_SQL)
        con.commit()
    finally:
        con.close()


class CustomerApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=16)
        self.master.title("Customer Information Management System")
        self.pack(fill="both", expand=True)

        # State variables
        self.var_name = tk.StringVar()
        self.var_bday = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_phone = tk.StringVar()
        self.var_contact = tk.StringVar(value="Email")

        # Layout
        self._build_form()
        self._build_buttons()

    def _label(self, parent, text, row, col=0, **kwargs):
        lbl = ttk.Label(parent, text=text)
        lbl.grid(row=row, column=col, sticky="w", padx=(0, 8), pady=6)
        return lbl

    def _build_form(self):
        frm = ttk.Frame(self)
        frm.pack(fill="x", expand=False)

        # Name
        self._label(frm, "Name *", 0)
        ent_name = ttk.Entry(frm, textvariable=self.var_name, width=40)
        ent_name.grid(row=0, column=1, sticky="ew")
        ent_name.focus()

        # Birthday
        self._label(frm, "Birthday (YYYY-MM-DD) *", 1)
        ent_bday = ttk.Entry(frm, textvariable=self.var_bday, width=20)
        ent_bday.grid(row=1, column=1, sticky="w")

        # Email
        self._label(frm, "Email *", 2)
        ent_email = ttk.Entry(frm, textvariable=self.var_email, width=40)
        ent_email.grid(row=2, column=1, sticky="ew")

        # Phone
        self._label(frm, "Phone *", 3)
        ent_phone = ttk.Entry(frm, textvariable=self.var_phone, width=30)
        ent_phone.grid(row=3, column=1, sticky="w")

        # Address
        self._label(frm, "Address *", 4)
        self.txt_address = tk.Text(frm, width=40, height=4, wrap="word")
        self.txt_address.grid(row=4, column=1, sticky="ew")

        # Preferred Contact
        self._label(frm, "Preferred Contact *", 5)
        cmb_contact = ttk.Combobox(
            frm,
            textvariable=self.var_contact,
            values=["Email", "Phone", "Mail"],
            state="readonly",
            width=18,
        )
        cmb_contact.grid(row=5, column=1, sticky="w")

        # Column weights for resizing
        frm.columnconfigure(0, weight=0)
        frm.columnconfigure(1, weight=1)

        # Hints
        hint = ttk.Label(
            self,
            text="Fields marked * are required. Your data is saved to customer_info.db",
            foreground="#666",
        )
        hint.pack(anchor="w", pady=(8, 0))

    def _build_buttons(self):
        btns = ttk.Frame(self)
        btns.pack(fill="x", expand=False, pady=(12, 0))

        btn_submit = ttk.Button(btns, text="Submit", command=self.on_submit)
        btn_submit.pack(side="left")

        btn_clear = ttk.Button(btns, text="Clear", command=self.clear_form)
        btn_clear.pack(side="left", padx=(8, 0))

        btn_quit = ttk.Button(btns, text="Quit", command=self.master.destroy)
        btn_quit.pack(side="right")

    # ---------- Validation Helpers ----------
    def _validate_name(self, name: str) -> bool:
        return bool(name.strip())

    def _validate_birthday(self, bday: str) -> bool:
        try:
            datetime.strptime(bday, "%Y-%m-%d")
            return True
        except Exception:
            return False

    def _validate_email(self, email: str) -> bool:
        return bool(EMAIL_RE.match(email))

    def _validate_phone(self, phone: str) -> bool:
        return bool(PHONE_RE.match(phone))

    def _validate_address(self, address: str) -> bool:
        return len(address.strip()) > 0

    # ---------- DB Insertion ----------
    def save_to_db(self, data: dict):
        con = sqlite3.connect(DB_PATH)
        try:
            with con:
                con.execute(
                    """
                    INSERT INTO customers (name, birthday, email, phone, address, preferred_contact)
                    VALUES (:name, :birthday, :email, :phone, :address, :preferred_contact);
                    """,
                    data,
                )
        finally:
            con.close()

    # ---------- UI Actions ----------
    def on_submit(self):
        name = self.var_name.get().strip()
        bday = self.var_bday.get().strip()
        email = self.var_email.get().strip()
        phone = self.var_phone.get().strip()
        address = self.txt_address.get("1.0", "end").strip()
        contact = self.var_contact.get().strip()

        # Validate
        errors = []
        if not self._validate_name(name):
            errors.append("• Name is required.")
        if not self._validate_birthday(bday):
            errors.append("• Birthday must be in YYYY-MM-DD format (e.g., 2001-04-09).")
        if not self._validate_email(email):
            errors.append("• Email appears invalid (e.g., name@example.com).")
        if not self._validate_phone(phone):
            errors.append("• Phone appears invalid (allow digits, spaces, +, -, parentheses).")
        if not self._validate_address(address):
            errors.append("• Address is required.")
        if contact not in {"Email", "Phone", "Mail"}:
            errors.append("• Preferred contact must be Email, Phone, or Mail.")

        if errors:
            messagebox.showerror("Please fix the following", "\n".join(errors))
            return

        # Save
        try:
            self.save_to_db(
                {
                    "name": name,
                    "birthday": bday,
                    "email": email,
                    "phone": phone,
                    "address": address,
                    "preferred_contact": contact,
                }
            )
            messagebox.showinfo("Success", "Customer information saved.")
            self.clear_form()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save data:\n{e}")

    def clear_form(self):
        self.var_name.set("")
        self.var_bday.set("")
        self.var_email.set("")
        self.var_phone.set("")
        self.var_contact.set("Email")
        self.txt_address.delete("1.0", "end")


def main():
    init_db()
    root = tk.Tk()
    # Use ttk theme for cleaner look
    try:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = CustomerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()