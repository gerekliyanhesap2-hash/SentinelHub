"""
Virüs Tarama Modülü (Heuristik)
---------------------------------
ÖNEMLİ: Bu gerçek bir antivirüs motoru DEĞİLDİR, imza veritabanı kullanmaz.
Sadece şüphe uyandıran BELİRTİLERE bakan basit bir tarama aracıdır:

1) Ağ Bağlantısı Sekmesi:
   Çalışan işlemlerin aktif ağ bağlantılarına bakar; uzak adres Telegram/
   Discord API'lerine benziyorsa VEYA işlem şüpheli bir klasörden (Temp,
   Downloads vb.) çalışıyorsa "şüpheli" olarak işaretler.

2) Dosya Taraması Sekmesi:
   Seçilen klasörü tarar; rastgele görünümlü isim, çift uzantı
   (örn. fatura.pdf.exe) veya şüpheli konum gibi belirtileri olan
   çalıştırılabilir dosyaları listeler.

Sonuçlar KESİN değildir, sadece "bunlara bir göz at" anlamına gelir.
Gereken kütüphane: psutil  ->  pip install psutil
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
import re
import socket
import threading

from modules import style as S
from modules.god_mode import make_scrollable_listbox  # aynı liste bileşenini tekrar kullan

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

SUSPICIOUS_KEYWORDS = ["telegram", "discord", "webhook", "pastebin", "ngrok"]
SUSPICIOUS_LOCATIONS = [
    os.sep + "temp" + os.sep,
    os.sep + "appdata" + os.sep + "local" + os.sep + "temp" + os.sep,
    os.sep + "downloads" + os.sep,
]
RANDOM_NAME_PATTERN = re.compile(r"^[a-f0-9]{8,}$", re.IGNORECASE)
DOUBLE_EXTENSION_PATTERN = re.compile(r"\.(pdf|docx?|xlsx?|jpg|png|txt|zip)\.(exe|scr|bat|cmd|vbs|js)$", re.IGNORECASE)
EXECUTABLE_EXTENSIONS = (".exe", ".scr", ".bat", ".cmd", ".vbs", ".js")


class VirusScanFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=S.BG)

        tk.Label(
            self, text="🛡 Virüs Tarama (Heuristik)", bg=S.BG, fg=S.TEXT, font=S.FONT_TITLE
        ).pack(anchor="w", pady=(0, 5))

        tk.Label(
            self,
            text="Bu araç imza tabanlı gerçek bir antivirüs değildir; sadece şüphe uyandıran davranış/desenlere bakar.",
            bg=S.BG, fg=S.WARNING, font=S.FONT_SMALL, wraplength=800, justify="left"
        ).pack(anchor="w", pady=(0, 15))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=S.BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=S.CARD, foreground=S.TEXT, padding=[14, 8])
        style.map("TNotebook.Tab", background=[("selected", S.ACCENT)], foreground=[("selected", "#1e1e2e")])

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self._build_network_tab(notebook)
        self._build_filescan_tab(notebook)

    # ---------------------------------------------------------
    def _build_network_tab(self, notebook):
        tab = tk.Frame(notebook, bg=S.BG)
        notebook.add(tab, text="Ağ Bağlantıları")

        header = tk.Frame(tab, bg=S.BG)
        header.pack(fill="x", pady=10, padx=5)
        tk.Label(
            header, text="Aktif bağlantısı olan işlemleri kontrol eder", bg=S.BG, fg=S.TEXT_MUTED, font=S.FONT_SMALL
        ).pack(side="left")
        self.network_scan_btn = tk.Button(
            header, text="🔄 Tara", command=self._start_network_scan,
            bg=S.CARD, fg=S.TEXT, font=S.FONT_SMALL, relief="flat", cursor="hand2"
        )
        self.network_scan_btn.pack(side="right")

        list_frame, self.network_list = make_scrollable_listbox(tab)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        if not PSUTIL_OK:
            self.network_list.insert(tk.END, "'psutil' kütüphanesi gerekli: pip install psutil")

    def _start_network_scan(self):
        if not PSUTIL_OK:
            return
        self.network_list.delete(0, tk.END)
        self.network_list.insert(tk.END, "Taranıyor, lütfen bekle (DNS sorguları biraz sürebilir)...")
        self.network_scan_btn.config(state="disabled")
        threading.Thread(target=self._network_scan_worker, daemon=True).start()

    def _network_scan_worker(self):
        flagged = []
        try:
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    connections = proc.net_connections(kind="inet") if hasattr(proc, "net_connections") else proc.connections(kind="inet")
                except Exception:
                    continue

                for c in connections:
                    if not c.raddr or c.status != "ESTABLISHED":
                        continue

                    reasons = []
                    remote_ip = c.raddr.ip

                    hostname = ""
                    try:
                        hostname = socket.gethostbyaddr(remote_ip)[0].lower()
                    except Exception:
                        hostname = ""

                    if any(k in hostname for k in SUSPICIOUS_KEYWORDS):
                        reasons.append(f"uzak adres '{hostname}' şüpheli bir servise benziyor")

                    exe_path = (proc.info.get("exe") or "").lower()
                    if any(loc in exe_path for loc in SUSPICIOUS_LOCATIONS):
                        reasons.append("dosya Temp/Downloads gibi geçici bir konumdan çalışıyor")

                    proc_name = (proc.info.get("name") or "")
                    name_no_ext = os.path.splitext(proc_name)[0]
                    if RANDOM_NAME_PATTERN.match(name_no_ext):
                        reasons.append("rastgele/şifreli görünümlü dosya adı")

                    if reasons:
                        flagged.append(
                            f"[PID {proc.info.get('pid')}] {proc_name}  ({remote_ip})\n"
                            f"      -> {', '.join(reasons)}\n"
                            f"      -> Yol: {proc.info.get('exe') or 'bilinmiyor'}"
                        )
        except Exception as e:
            flagged = [f"Tarama sırasında hata oluştu: {e}"]

        def apply():
            self.network_list.delete(0, tk.END)
            if not flagged:
                self.network_list.insert(tk.END, "Şüpheli bir ağ bağlantısı bulunamadı. ✔")
            else:
                for line in flagged:
                    for sub in line.split("\n"):
                        self.network_list.insert(tk.END, sub)
                    self.network_list.insert(tk.END, "")
            self.network_scan_btn.config(state="normal")

        self.after(0, apply)

    # ---------------------------------------------------------
    def _build_filescan_tab(self, notebook):
        tab = tk.Frame(notebook, bg=S.BG)
        notebook.add(tab, text="Dosya Taraması")

        header = tk.Frame(tab, bg=S.BG)
        header.pack(fill="x", pady=10, padx=5)
        self.filescan_folder_var = tk.StringVar(value="Klasör seçilmedi (öneri: İndirilenler / Temp)")
        tk.Label(header, textvariable=self.filescan_folder_var, bg=S.BG, fg=S.TEXT_MUTED, font=S.FONT_SMALL).pack(side="left")
        tk.Button(
            header, text="📁 Klasör Seç ve Tara", command=self._start_file_scan,
            bg=S.CARD, fg=S.TEXT, font=S.FONT_SMALL, relief="flat", cursor="hand2"
        ).pack(side="right")

        list_frame, self.filescan_list = make_scrollable_listbox(tab)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def _start_file_scan(self):
        folder = filedialog.askdirectory(title="Taranacak klasörü seç")
        if not folder:
            return
        self.filescan_folder_var.set(folder)
        self.filescan_list.delete(0, tk.END)
        self.filescan_list.insert(tk.END, "Taranıyor...")
        threading.Thread(target=self._file_scan_worker, args=(folder,), daemon=True).start()

    def _file_scan_worker(self, folder):
        flagged = []
        try:
            for root, dirs, files in os.walk(folder):
                lower_root = root.lower()
                for name in files:
                    ext = os.path.splitext(name)[1].lower()
                    if ext not in EXECUTABLE_EXTENSIONS:
                        continue

                    full_path = os.path.join(root, name)
                    reasons = []

                    name_no_ext = os.path.splitext(name)[0]
                    if RANDOM_NAME_PATTERN.match(name_no_ext):
                        reasons.append("rastgele/şifreli görünümlü isim")

                    if DOUBLE_EXTENSION_PATTERN.search(name.lower()):
                        reasons.append("çift uzantı (örn. belge.pdf.exe) - klasik gizleme yöntemi")

                    if any(loc.strip(os.sep) in lower_root for loc in SUSPICIOUS_LOCATIONS):
                        reasons.append("şüpheli konumda (Temp/Downloads)")

                    if reasons:
                        flagged.append(f"{full_path}\n      -> {', '.join(reasons)}")

                if sum(1 for _ in flagged) > 1000:
                    break
        except Exception as e:
            flagged = [f"Tarama sırasında hata oluştu: {e}"]

        def apply():
            self.filescan_list.delete(0, tk.END)
            if not flagged:
                self.filescan_list.insert(tk.END, "Şüpheli dosya bulunamadı. ✔")
            else:
                for line in flagged:
                    for sub in line.split("\n"):
                        self.filescan_list.insert(tk.END, sub)
                    self.filescan_list.insert(tk.END, "")

        self.after(0, apply)