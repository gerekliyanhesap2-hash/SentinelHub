"""
Dosya Arama Modülü
-------------------
Seçilen klasör (veya sürücü) içinde dosya adına göre hızlı arama yapar.
Not: "Everything" programı NTFS Master File Table'ı okuyarak anlık sonuç verir.
Biz standart Python ile bunu yapamayız; bunun yerine dosya sistemini tarayıp
sonuçları anlık olarak listeye ekleyen, arayüzü kilitlemeyen (thread kullanan)
bir arama yapıyoruz. İlk taramadan sonra sonuçlar bellekte tutulur, bu yüzden
aynı klasörde tekrar arama yapmak çok daha hızlı olur.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
import threading
import subprocess
import platform

COLOR_BG = "#1e1e2e"
COLOR_CARD = "#313244"
COLOR_TEXT = "#cdd6f4"
COLOR_TEXT_MUTED = "#a6adc8"
COLOR_ACCENT = "#89b4fa"

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_NORMAL = ("Segoe UI", 11)


class FileSearchFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_BG)

        self.all_files = []          # (dosya_adi, tam_yol) listesi - önbellek
        self.indexed_folder = None
        self.search_thread = None
        self.stop_flag = threading.Event()

        # Başlık
        tk.Label(
            self, text="🔍 Dosya Arama", bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_TITLE
        ).pack(anchor="w", pady=(0, 20))

        # --- Klasör seçimi ---
        folder_frame = tk.Frame(self, bg=COLOR_BG)
        folder_frame.pack(fill="x", pady=(0, 10))

        self.folder_var = tk.StringVar(value="Henüz klasör seçilmedi")
        tk.Label(
            folder_frame, textvariable=self.folder_var, bg=COLOR_BG, fg=COLOR_TEXT_MUTED,
            font=FONT_NORMAL, anchor="w"
        ).pack(side="left", fill="x", expand=True)

        tk.Button(
            folder_frame, text="📁 Klasör Seç", command=self.choose_folder,
            bg=COLOR_CARD, fg=COLOR_TEXT, font=FONT_NORMAL, relief="flat", cursor="hand2"
        ).pack(side="right")

        # --- Arama kutusu ---
        search_frame = tk.Frame(self, bg=COLOR_BG)
        search_frame.pack(fill="x", pady=10)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_change)

        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var, font=("Segoe UI", 13),
            bg=COLOR_CARD, fg=COLOR_TEXT, insertbackground=COLOR_TEXT, relief="flat"
        )
        search_entry.pack(fill="x", ipady=8)
        search_entry.insert(0, "")
        search_entry.focus()

        # --- Durum etiketi ---
        self.status_var = tk.StringVar(value="Arama yapmak için önce bir klasör seç.")
        tk.Label(
            self, textvariable=self.status_var, bg=COLOR_BG, fg=COLOR_TEXT_MUTED, font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(5, 10))

        # --- Sonuç listesi ---
        list_frame = tk.Frame(self, bg=COLOR_BG)
        list_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.result_list = tk.Listbox(
            list_frame, bg=COLOR_CARD, fg=COLOR_TEXT, font=("Consolas", 10),
            selectbackground=COLOR_ACCENT, relief="flat", yscrollcommand=scrollbar.set
        )
        self.result_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.result_list.yview)

        self.result_list.bind("<Double-Button-1>", self.open_selected_file_location)

    # -------------------------------------------------------------
    def choose_folder(self):
        folder = filedialog.askdirectory(title="Aranacak klasörü seç")
        if not folder:
            return
        self.folder_var.set(folder)
        self.indexed_folder = folder
        self.all_files = []
        self.result_list.delete(0, tk.END)
        self.status_var.set("Klasör taranıyor, lütfen bekle...")
        self.stop_flag.set()  # varsa önceki taramayı durdur

        self.stop_flag = threading.Event()
        self.search_thread = threading.Thread(
            target=self._index_folder, args=(folder, self.stop_flag), daemon=True
        )
        self.search_thread.start()

    def _index_folder(self, folder, stop_flag):
        count = 0
        for root, dirs, files in os.walk(folder):
            if stop_flag.is_set():
                return
            for name in files:
                self.all_files.append((name, os.path.join(root, name)))
                count += 1
            if count % 500 == 0:
                self.status_var.set(f"Taranıyor... {count} dosya bulundu")

        self.status_var.set(f"Tarama tamamlandı. Toplam {count} dosya indexlendi.")
        # Tarama bitince mevcut arama terimiyle sonuçları göster
        self.after(0, self.refresh_results)

    def on_search_change(self, *args):
        self.refresh_results()

    def refresh_results(self):
        query = self.search_var.get().strip().lower()
        self.result_list.delete(0, tk.END)

        if not self.all_files:
            return

        if not query:
            matches = self.all_files[:500]  # boşken ilk 500 dosyayı göster
        else:
            matches = [f for f in self.all_files if query in f[0].lower()][:500]

        for name, full_path in matches:
            self.result_list.insert(tk.END, f"{name}    —    {full_path}")

        if query:
            self.status_var.set(f"{len(matches)} sonuç bulundu (en fazla 500 gösterilir)")

    def open_selected_file_location(self, event):
        selection = self.result_list.curselection()
        if not selection:
            return
        item_text = self.result_list.get(selection[0])
        full_path = item_text.split("    —    ", 1)[-1]
        folder = os.path.dirname(full_path)

        system = platform.system()
        try:
            if system == "Windows":
                # Dosyayı gezginde seçili olarak açar
                subprocess.run(["explorer", "/select,", full_path])
            elif system == "Darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
        except Exception as e:
            self.status_var.set(f"Klasör açılamadı: {e}")
