"""
SentinelHub - Ana Uygulama
----------------------------
Windows için çok amaçlı sistem/güvenlik araç kutusu.
Sol tarafta menü (sidebar), sağ tarafta seçilen aracın ekranı bulunur.

Yeni bir araç eklemek için:
1. modules/ klasörüne yeni bir .py dosyası ekle
2. O dosyada bir tkinter.Frame sınıfı oluştur (modules/style.py'daki renkleri kullan)
3. Aşağıdaki TOOLS listesine ekle
"""

import tkinter as tk

from modules.dashboard import DashboardFrame
from modules.network_speed import NetworkSpeedFrame
from modules.ip_info import IPInfoFrame
from modules.password_generator import PasswordGeneratorFrame
from modules.file_search import FileSearchFrame
from modules.god_mode import GodModeFrame
from modules.virus_scan import VirusScanFrame
from modules import style as S

FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_MENU = ("Segoe UI", 12)

# Sırayla sidebar'da görünür. İlk eleman açılışta gösterilir.
TOOLS = [
    ("Sistem Paneli", "📊", DashboardFrame),
    ("Ağ Hız Testi", "🚀", NetworkSpeedFrame),
    ("IP Adresim", "🌐", IPInfoFrame),
    ("Şifre Oluşturucu", "🔐", PasswordGeneratorFrame),
    ("Dosya Arama", "🔍", FileSearchFrame),
    ("God Mode", "👁", GodModeFrame),
    ("Virüs Tarama", "🛡", VirusScanFrame),
]


class SentinelHub(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SentinelHub")
        self.geometry("1000x650")
        self.minsize(850, 550)
        self.configure(bg=S.BG)

        self.current_frame = None
        self.menu_buttons = []
        self.active_index = -1

        self._build_sidebar()
        self._build_content_area()
        self._show_tool(0)

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=S.CARD, width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar, text="🛡 SentinelHub",
            bg=S.CARD, fg=S.TEXT, font=FONT_TITLE, pady=25
        ).pack(fill="x")

        for index, (name, icon, _) in enumerate(TOOLS):
            btn = tk.Label(
                self.sidebar,
                text=f"  {icon}   {name}",
                bg=S.CARD,
                fg=S.TEXT_MUTED,
                font=FONT_MENU,
                anchor="w",
                padx=15,
                pady=12,
                cursor="hand2",
            )
            btn.pack(fill="x")
            btn.bind("<Button-1>", lambda e, i=index: self._show_tool(i))
            btn.bind("<Enter>", lambda e, b=btn, i=index: self._on_hover(b, i, True))
            btn.bind("<Leave>", lambda e, b=btn, i=index: self._on_hover(b, i, False))
            self.menu_buttons.append(btn)

        tk.Label(
            self.sidebar, text="v0.2.0", bg=S.CARD, fg=S.TEXT_MUTED, font=("Segoe UI", 9)
        ).pack(side="bottom", pady=10)

    def _on_hover(self, btn, index, entering):
        if index == self.active_index:
            return
        btn.configure(bg=S.CARD_LIGHT if entering else S.CARD)

    def _build_content_area(self):
        self.content = tk.Frame(self, bg=S.BG)
        self.content.pack(side="right", fill="both", expand=True)

    def _show_tool(self, index):
        if self.current_frame is not None:
            self.current_frame.destroy()

        for i, btn in enumerate(self.menu_buttons):
            if i == index:
                btn.configure(bg=S.CARD_LIGHT, fg=S.ACCENT)
            else:
                btn.configure(bg=S.CARD, fg=S.TEXT_MUTED)
        self.active_index = index

        _, _, frame_class = TOOLS[index]
        self.current_frame = frame_class(self.content)
        self.current_frame.pack(fill="both", expand=True, padx=30, pady=25)


if __name__ == "__main__":
    app = SentinelHub()
    app.mainloop()