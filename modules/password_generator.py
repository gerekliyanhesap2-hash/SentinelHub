"""
Şifre Oluşturucu Modülü
------------------------
Kullanıcının belirlediği kriterlere göre güvenli, rastgele şifre üretir.
"""

import tkinter as tk
from tkinter import ttk
import random
import string

COLOR_BG = "#1e1e2e"
COLOR_CARD = "#313244"
COLOR_TEXT = "#cdd6f4"
COLOR_ACCENT = "#89b4fa"
COLOR_SUCCESS = "#a6e3a1"

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_NORMAL = ("Segoe UI", 11)
FONT_PASSWORD = ("Consolas", 18, "bold")


class PasswordGeneratorFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG)

        # Başlık
        tk.Label(
            self, text="🔐 Şifre Oluşturucu", bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_TITLE
        ).pack(anchor="w", pady=(0, 20))

        # --- Uzunluk ayarı ---
        length_frame = tk.Frame(self, bg=COLOR_BG)
        length_frame.pack(fill="x", pady=10)

        tk.Label(
            length_frame, text="Şifre Uzunluğu:", bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_NORMAL
        ).pack(side="left")

        self.length_var = tk.IntVar(value=16)
        self.length_label = tk.Label(
            length_frame, textvariable=self.length_var, bg=COLOR_BG, fg=COLOR_ACCENT,
            font=("Segoe UI", 11, "bold"), width=3
        )
        self.length_label.pack(side="right")

        self.length_scale = tk.Scale(
            length_frame, from_=4, to=64, orient="horizontal",
            variable=self.length_var, bg=COLOR_BG, fg=COLOR_TEXT,
            troughcolor=COLOR_CARD, highlightthickness=0, showvalue=False,
            activebackground=COLOR_ACCENT
        )
        self.length_scale.pack(side="left", fill="x", expand=True, padx=10)

        # --- Karakter seçenekleri ---
        options_frame = tk.Frame(self, bg=COLOR_BG)
        options_frame.pack(fill="x", pady=15)

        self.use_upper = tk.BooleanVar(value=True)
        self.use_lower = tk.BooleanVar(value=True)
        self.use_digits = tk.BooleanVar(value=True)
        self.use_symbols = tk.BooleanVar(value=True)
        self.avoid_ambiguous = tk.BooleanVar(value=False)

        checks = [
            ("Büyük harf (A-Z)", self.use_upper),
            ("Küçük harf (a-z)", self.use_lower),
            ("Rakam (0-9)", self.use_digits),
            ("Sembol (!@#$...)", self.use_symbols),
            ("Karışabilecek karakterleri hariç tut (l, 1, O, 0)", self.avoid_ambiguous),
        ]

        for text, var in checks:
            cb = tk.Checkbutton(
                options_frame, text=text, variable=var,
                bg=COLOR_BG, fg=COLOR_TEXT, selectcolor=COLOR_CARD,
                activebackground=COLOR_BG, activeforeground=COLOR_TEXT,
                font=FONT_NORMAL, anchor="w"
            )
            cb.pack(fill="x", pady=3)

        # --- Oluştur butonu ---
        generate_btn = tk.Button(
            self, text="Şifre Oluştur", command=self.generate_password,
            bg=COLOR_ACCENT, fg="#1e1e2e", font=("Segoe UI", 12, "bold"),
            relief="flat", cursor="hand2", pady=8
        )
        generate_btn.pack(fill="x", pady=(20, 15))

        # --- Sonuç kutusu ---
        result_card = tk.Frame(self, bg=COLOR_CARD)
        result_card.pack(fill="x", pady=5)

        self.result_var = tk.StringVar(value="Şifre burada görünecek")
        result_label = tk.Label(
            result_card, textvariable=self.result_var, bg=COLOR_CARD, fg=COLOR_ACCENT,
            font=FONT_PASSWORD, pady=20, wraplength=500
        )
        result_label.pack(side="left", fill="x", expand=True, padx=15)

        copy_btn = tk.Button(
            result_card, text="📋 Kopyala", command=self.copy_to_clipboard,
            bg=COLOR_CARD, fg=COLOR_TEXT, font=FONT_NORMAL,
            relief="flat", cursor="hand2"
        )
        copy_btn.pack(side="right", padx=15)

        self.status_var = tk.StringVar(value="")
        tk.Label(
            self, textvariable=self.status_var, bg=COLOR_BG, fg=COLOR_SUCCESS, font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(5, 0))

        # Sekme açılır açılmaz bir şifre üret
        self.generate_password()

    # -------------------------------------------------------------
    def generate_password(self):
        pool = ""
        if self.use_upper.get():
            pool += string.ascii_uppercase
        if self.use_lower.get():
            pool += string.ascii_lowercase
        if self.use_digits.get():
            pool += string.digits
        if self.use_symbols.get():
            pool += "!@#$%^&*()-_=+[]{};:,.<>?"

        if self.avoid_ambiguous.get():
            for ch in "l1IO0":
                pool = pool.replace(ch, "")

        if not pool:
            self.result_var.set("En az bir karakter türü seçmelisin!")
            return

        length = self.length_var.get()
        password = "".join(random.SystemRandom().choice(pool) for _ in range(length))

        self.result_var.set(password)
        self.status_var.set("")

    def copy_to_clipboard(self):
        password = self.result_var.get()
        self.clipboard_clear()
        self.clipboard_append(password)
        self.status_var.set("✔ Panoya kopyalandı!")
