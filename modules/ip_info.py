"""
IP Adresim Modülü
-------------------
Genel (public) IP adresini, yerel ağ IP adresini ve yaklaşık konum/ISS
bilgisini gösterir.

Gereken kütüphane: requests  ->  pip install requests
"""

import tkinter as tk
import socket
import threading

from modules import style as S

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


class InfoRow(tk.Frame):
    def __init__(self, parent, label, value="Alınıyor..."):
        super().__init__(parent, bg=S.CARD, padx=20, pady=14)
        tk.Label(self, text=label, bg=S.CARD, fg=S.TEXT_MUTED, font=S.FONT_NORMAL, width=18, anchor="w").pack(side="left")
        self.value_var = tk.StringVar(value=value)
        tk.Label(self, textvariable=self.value_var, bg=S.CARD, fg=S.TEXT, font=("Segoe UI", 12, "bold"), anchor="w").pack(side="left", fill="x", expand=True)

    def set(self, value):
        self.value_var.set(value)


class IPInfoFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=S.BG)

        tk.Label(
            self, text="🌐 IP Adresim", bg=S.BG, fg=S.TEXT, font=S.FONT_TITLE
        ).pack(anchor="w", pady=(0, 20))

        self.rows = {}
        for key, title in [
            ("public_ip", "Genel (Public) IP"),
            ("local_ip", "Yerel Ağ IP"),
            ("isp", "İnternet Sağlayıcısı"),
            ("location", "Yaklaşık Konum"),
        ]:
            row = InfoRow(self, title)
            row.pack(fill="x", pady=4)
            self.rows[key] = row

        tk.Button(
            self, text="🔄 Yenile", command=self.refresh,
            bg=S.CARD, fg=S.TEXT, font=S.FONT_NORMAL, relief="flat", cursor="hand2"
        ).pack(anchor="w", pady=20)

        if not REQUESTS_OK:
            tk.Label(
                self, text="⚠ 'requests' kütüphanesi bulunamadı. Kurmak için: pip install requests",
                bg=S.BG, fg=S.WARNING, font=S.FONT_NORMAL
            ).pack(anchor="w", pady=10)

        # Yerel IP'yi hemen göster (ağ gerektirmez)
        self.rows["local_ip"].set(self._get_local_ip())

        if REQUESTS_OK:
            self.refresh()

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Alınamadı"

    def refresh(self):
        for key in ["public_ip", "isp", "location"]:
            self.rows[key].set("Alınıyor...")
        threading.Thread(target=self._fetch_public_info, daemon=True).start()

    def _fetch_public_info(self):
        try:
            resp = requests.get("https://ipapi.co/json/", timeout=6)
            data = resp.json()

            public_ip = data.get("ip", "Alınamadı")
            isp = data.get("org", "Alınamadı")
            city = data.get("city", "")
            region = data.get("region", "")
            country = data.get("country_name", "")
            location = ", ".join([p for p in [city, region, country] if p]) or "Alınamadı"

            self.after(0, lambda: self.rows["public_ip"].set(public_ip))
            self.after(0, lambda: self.rows["isp"].set(isp))
            self.after(0, lambda: self.rows["location"].set(location))
        except Exception as e:
            self.after(0, lambda: self.rows["public_ip"].set(f"Alınamadı ({e})"))
            self.after(0, lambda: self.rows["isp"].set("Alınamadı"))
            self.after(0, lambda: self.rows["location"].set("Alınamadı"))