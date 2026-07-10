"""
God Mode Modülü
-----------------
Normalde kolayca görünmeyen sistem bilgilerini tek ekranda toplar:
  - Gizli dosya/klasörler (seçilen klasör içinde)
  - Başlangıçta otomatik çalışan programlar (Registry Run anahtarları + Startup klasörü)
  - Windows servisleri ve durumları
  - Yüklü programlar (Registry Uninstall anahtarlarından)
  - Açık/dinlemedeki ağ portları
  - Yönetici yetkisi gerektiren gizli sistem klasörleri

Gereken kütüphane: psutil  ->  pip install psutil
Not: Bazı sekmeler (servisler, başlangıç programları, gizli sistem klasörleri)
sadece Windows'ta tam olarak çalışır. Bazı bilgiler için programı
"Yönetici olarak çalıştır" ile açman gerekebilir.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
import platform
import threading

from modules import style as S

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import ctypes
    try:
        import winreg
    except ImportError:
        winreg = None
else:
    winreg = None

# Windows'ta genelde admin yetkisi istenen / gizli tutulan klasörler
ADMIN_PROTECTED_PATHS = [
    r"C:\Windows\System32\config",
    r"C:\Windows\CSC",
    r"C:\System Volume Information",
    r"C:\ProgramData\Microsoft\Windows\WER",
    r"C:\Windows\SoftwareDistribution\Download",
    r"C:\Users\All Users",
    r"C:\Windows\Prefetch",
]


def make_scrollable_listbox(parent):
    frame = tk.Frame(parent, bg=S.BG)
    scrollbar = tk.Scrollbar(frame)
    scrollbar.pack(side="right", fill="y")
    listbox = tk.Listbox(
        frame, bg=S.CARD, fg=S.TEXT, font=S.FONT_MONO, relief="flat",
        selectbackground=S.ACCENT, yscrollcommand=scrollbar.set
    )
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=listbox.yview)
    return frame, listbox


class GodModeFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=S.BG)

        tk.Label(
            self, text="👁 God Mode", bg=S.BG, fg=S.TEXT, font=S.FONT_TITLE
        ).pack(anchor="w", pady=(0, 5))

        tk.Label(
            self, text="Normalde kolay görünmeyen sistem bilgileri. Tam sonuç için 'Yönetici olarak çalıştır' önerilir.",
            bg=S.BG, fg=S.TEXT_MUTED, font=S.FONT_SMALL
        ).pack(anchor="w", pady=(0, 15))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=S.BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=S.CARD, foreground=S.TEXT, padding=[14, 8])
        style.map("TNotebook.Tab", background=[("selected", S.ACCENT)], foreground=[("selected", "#1e1e2e")])

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        self._build_hidden_files_tab(notebook)
        self._build_startup_tab(notebook)
        self._build_services_tab(notebook)
        self._build_installed_programs_tab(notebook)
        self._build_ports_tab(notebook)
        self._build_protected_folders_tab(notebook)

    # ---------------------------------------------------------
    def _tab_header(self, parent, description, scan_command):
        header = tk.Frame(parent, bg=S.BG)
        header.pack(fill="x", pady=(10, 5), padx=5)
        tk.Label(header, text=description, bg=S.BG, fg=S.TEXT_MUTED, font=S.FONT_SMALL).pack(side="left")
        tk.Button(
            header, text="🔄 Tara", command=scan_command,
            bg=S.CARD, fg=S.TEXT, font=S.FONT_SMALL, relief="flat", cursor="hand2"
        ).pack(side="right")

    # ---------------------------------------------------------
    def _build_hidden_files_tab(self, notebook):
        tab = tk.Frame(notebook, bg=S.BG)
        notebook.add(tab, text="Gizli Dosyalar")

        header = tk.Frame(tab, bg=S.BG)
        header.pack(fill="x", pady=10, padx=5)

        self.hidden_folder_var = tk.StringVar(value="Klasör seçilmedi")
        tk.Label(header, textvariable=self.hidden_folder_var, bg=S.BG, fg=S.TEXT_MUTED, font=S.FONT_SMALL).pack(side="left")
        tk.Button(
            header, text="📁 Klasör Seç ve Tara", command=self._scan_hidden_files,
            bg=S.CARD, fg=S.TEXT, font=S.FONT_SMALL, relief="flat", cursor="hand2"
        ).pack(side="right")

        list_frame, self.hidden_files_list = make_scrollable_listbox(tab)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def _scan_hidden_files(self):
        folder = filedialog.askdirectory(title="Gizli dosyaları taramak için klasör seç")
        if not folder:
            return
        self.hidden_folder_var.set(folder)
        self.hidden_files_list.delete(0, tk.END)
        self.hidden_files_list.insert(tk.END, "Taranıyor...")
        threading.Thread(target=self._hidden_files_worker, args=(folder,), daemon=True).start()

    def _is_hidden(self, path):
        name = os.path.basename(path)
        if name.startswith("."):
            return True
        if IS_WINDOWS:
            try:
                FILE_ATTRIBUTE_HIDDEN = 0x2
                FILE_ATTRIBUTE_SYSTEM = 0x4
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
                if attrs == -1:
                    return False
                return bool(attrs & (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM))
            except Exception:
                return False
        return False

    def _hidden_files_worker(self, folder):
        results = []
        try:
            for root, dirs, files in os.walk(folder):
                for name in list(dirs) + files:
                    full_path = os.path.join(root, name)
                    if self._is_hidden(full_path):
                        results.append(full_path)
                if len(results) > 2000:
                    break
        except Exception:
            pass

        def apply():
            self.hidden_files_list.delete(0, tk.END)
            if not results:
                self.hidden_files_list.insert(tk.END, "Gizli dosya/klasör bulunamadı.")
            for r in results[:2000]:
                self.hidden_files_list.insert(tk.END, r)

        self.after(0, apply)

    # ---------------------------------------------------------
    def _build_startup_tab(self, notebook):
        tab = tk.Frame(notebook, bg=S.BG)
        notebook.add(tab, text="Başlangıç Programları")
        self._tab_header(tab, "Bilgisayar açılırken otomatik çalışan programlar", self._scan_startup)
        list_frame, self.startup_list = make_scrollable_listbox(tab)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._scan_startup()

    def _scan_startup(self):
        self.startup_list.delete(0, tk.END)
        if not IS_WINDOWS or winreg is None:
            self.startup_list.insert(tk.END, "Bu özellik sadece Windows'ta çalışır.")
            return

        entries = []
        run_key_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        ]
        for hive, path in run_key_paths:
            try:
                with winreg.OpenKey(hive, path) as key:
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            entries.append(f"{name}  ->  {value}")
                            i += 1
                        except OSError:
                            break
            except Exception:
                continue

        # Startup klasörü
        startup_folder = os.path.join(
            os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup"
        )
        if os.path.isdir(startup_folder):
            try:
                for f in os.listdir(startup_folder):
                    entries.append(f"[Startup klasörü] {f}")
            except Exception:
                pass

        if not entries:
            entries = ["Başlangıç programı bulunamadı."]
        for e in entries:
            self.startup_list.insert(tk.END, e)

    # ---------------------------------------------------------
    def _build_services_tab(self, notebook):
        tab = tk.Frame(notebook, bg=S.BG)
        notebook.add(tab, text="Servisler")
        self._tab_header(tab, "Windows servisleri ve çalışma durumları", self._scan_services)
        list_frame, self.services_list = make_scrollable_listbox(tab)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._scan_services()

    def _scan_services(self):
        self.services_list.delete(0, tk.END)
        if not (IS_WINDOWS and PSUTIL_OK and hasattr(psutil, "win_service_iter")):
            self.services_list.insert(tk.END, "Bu özellik sadece Windows'ta (psutil ile) çalışır.")
            return
        try:
            services = sorted(psutil.win_service_iter(), key=lambda s: s.name().lower())
            for s in services:
                try:
                    info = s.as_dict()
                    self.services_list.insert(tk.END, f"[{info['status'].upper():<10}] {info['display_name']}")
                except Exception:
                    continue
        except Exception as e:
            self.services_list.insert(tk.END, f"Hata: {e}")

    # ---------------------------------------------------------
    def _build_installed_programs_tab(self, notebook):
        tab = tk.Frame(notebook, bg=S.BG)
        notebook.add(tab, text="Yüklü Programlar")
        self._tab_header(tab, "Kayıt defterinden okunan yüklü program listesi", self._scan_installed_programs)
        list_frame, self.installed_list = make_scrollable_listbox(tab)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._scan_installed_programs()

    def _scan_installed_programs(self):
        self.installed_list.delete(0, tk.END)
        if not IS_WINDOWS or winreg is None:
            self.installed_list.insert(tk.END, "Bu özellik sadece Windows'ta çalışır.")
            return

        uninstall_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        names = set()
        for hive, path in uninstall_paths:
            try:
                with winreg.OpenKey(hive, path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        subkey_name = winreg.EnumKey(key, i)
                        try:
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    names.add(display_name)
                                except FileNotFoundError:
                                    continue
                        except Exception:
                            continue
            except Exception:
                continue

        if not names:
            self.installed_list.insert(tk.END, "Program bulunamadı.")
        for name in sorted(names, key=str.lower):
            self.installed_list.insert(tk.END, name)

    # ---------------------------------------------------------
    def _build_ports_tab(self, notebook):
        tab = tk.Frame(notebook, bg=S.BG)
        notebook.add(tab, text="Açık Portlar")
        self._tab_header(tab, "Dinlemede olan (LISTEN) ağ portları", self._scan_ports)
        list_frame, self.ports_list = make_scrollable_listbox(tab)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._scan_ports()

    def _scan_ports(self):
        self.ports_list.delete(0, tk.END)
        if not PSUTIL_OK:
            self.ports_list.insert(tk.END, "'psutil' kütüphanesi gerekli: pip install psutil")
            return
        try:
            conns = psutil.net_connections(kind="inet")
            listening = [c for c in conns if c.status == "LISTEN"]
            if not listening:
                self.ports_list.insert(tk.END, "Dinlemede port bulunamadı (yetki gerekebilir).")
            for c in listening:
                try:
                    proc_name = psutil.Process(c.pid).name() if c.pid else "Bilinmiyor"
                except Exception:
                    proc_name = "Bilinmiyor"
                addr = f"{c.laddr.ip}:{c.laddr.port}"
                self.ports_list.insert(tk.END, f"Port {c.laddr.port:<6} | {addr:<22} | {proc_name}")
        except Exception as e:
            self.ports_list.insert(tk.END, f"Hata (yönetici yetkisi gerekebilir): {e}")

    # ---------------------------------------------------------
    def _build_protected_folders_tab(self, notebook):
        tab = tk.Frame(notebook, bg=S.BG)
        notebook.add(tab, text="Gizli Sistem Klasörleri")
        self._tab_header(tab, "Genelde yönetici yetkisi gerektiren sistem klasörleri", self._scan_protected_folders)
        list_frame, self.protected_list = make_scrollable_listbox(tab)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self._scan_protected_folders()

    def _scan_protected_folders(self):
        self.protected_list.delete(0, tk.END)
        if not IS_WINDOWS:
            self.protected_list.insert(tk.END, "Bu özellik sadece Windows'ta çalışır.")
            return
        for path in ADMIN_PROTECTED_PATHS:
            exists = os.path.isdir(path)
            accessible = False
            if exists:
                try:
                    os.listdir(path)
                    accessible = True
                except Exception:
                    accessible = False
            status = "erişilebilir ✔" if accessible else ("erişim reddedildi (admin gerekli) 🔒" if exists else "bulunamadı")
            self.protected_list.insert(tk.END, f"{path}   —   {status}")