"""
Ağ Hız Testi Modülü
---------------------
Ping / İndirme (Download) / Yükleme (Upload) hızını ölçer, sonuçları
sayaç animasyonuyla gösterir.

Gereken kütüphane: speedtest-cli  ->  pip install speedtest-cli
(Bu kütüphane Speedtest.net altyapısını kullanarak gerçekçi sonuç verir.)
"""

import tkinter as tk
import threading
import math

from modules import style as S

try:
    import speedtest
    SPEEDTEST_OK = True
except ImportError:
    SPEEDTEST_OK = False


class AnimatedNumber(tk.Canvas):
    """Bir değeri 0'dan hedefe doğru sayarak gösteren, dönen bir yükleme
    halkasıyla birlikte çalışan gösterge."""

    def __init__(self, parent, label, unit="Mbps", color=S.ACCENT, size=160):
        super().__init__(parent, width=size, height=size, bg=S.BG, highlightthickness=0)
        self.size = size
        self.label = label
        self.unit = unit
        self.color = color
        self.value = 0.0
        self.target = None       # None = henüz ölçülmedi -> spinner göster
        self.spin_angle = 0
        self.busy = False
        self._draw()
        self._tick()

    def start_measuring(self):
        self.busy = True
        self.target = None
        self.value = 0.0

    def set_result(self, value):
        self.target = value
        self.busy = False

    def _tick(self):
        if self.busy and self.target is None:
            self.spin_angle = (self.spin_angle + 12) % 360
        elif self.target is not None and self.value < self.target:
            diff = self.target - self.value
            self.value += max(diff * 0.12, 0.05)
            if self.value > self.target:
                self.value = self.target
        self._draw()
        self.after(30, self._tick)

    def _draw(self):
        self.delete("all")
        pad = 12
        x0, y0 = pad, pad
        x1, y1 = self.size - pad, self.size - pad

        self.create_oval(x0, y0, x1, y1, outline=S.CARD_LIGHT, width=8)

        if self.busy and self.target is None:
            # Dönen spinner (belirsiz süre animasyonu)
            self.create_arc(
                x0, y0, x1, y1, start=self.spin_angle, extent=70,
                style="arc", outline=self.color, width=8
            )
            text = "..."
        else:
            text = f"{self.value:.1f}"

        self.create_text(
            self.size / 2, self.size / 2 - 10,
            text=text, fill=S.TEXT, font=S.FONT_BIG_NUMBER
        )
        self.create_text(
            self.size / 2, self.size / 2 + 18,
            text=self.unit, fill=S.TEXT_MUTED, font=S.FONT_SMALL
        )
        self.create_text(
            self.size / 2, self.size + 4,
            text=self.label, fill=S.TEXT, font=S.FONT_SUBTITLE, anchor="n"
        )


class NetworkSpeedFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=S.BG)

        tk.Label(
            self, text="🚀 Ağ Hız Testi", bg=S.BG, fg=S.TEXT, font=S.FONT_TITLE
        ).pack(anchor="w", pady=(0, 5))

        if not SPEEDTEST_OK:
            tk.Label(
                self, text="⚠ 'speedtest-cli' kütüphanesi bulunamadı. Kurmak için: pip install speedtest-cli",
                bg=S.BG, fg=S.WARNING, font=S.FONT_NORMAL
            ).pack(anchor="w", pady=10)
            return

        self.status_var = tk.StringVar(value="Teste başlamak için butona bas")
        tk.Label(
            self, textvariable=self.status_var, bg=S.BG, fg=S.TEXT_MUTED, font=S.FONT_NORMAL
        ).pack(anchor="w", pady=(0, 25))

        gauges_frame = tk.Frame(self, bg=S.BG)
        gauges_frame.pack(pady=10)

        self.ping_gauge = AnimatedNumber(gauges_frame, "Ping", unit="ms", color=S.WARNING)
        self.ping_gauge.grid(row=0, column=0, padx=30)

        self.download_gauge = AnimatedNumber(gauges_frame, "İndirme", unit="Mbps", color=S.ACCENT)
        self.download_gauge.grid(row=0, column=1, padx=30)

        self.upload_gauge = AnimatedNumber(gauges_frame, "Yükleme", unit="Mbps", color=S.SUCCESS)
        self.upload_gauge.grid(row=0, column=2, padx=30)

        self.start_btn = tk.Button(
            self, text="▶ Testi Başlat", command=self.start_test,
            bg=S.ACCENT, fg="#1e1e2e", font=("Segoe UI", 12, "bold"),
            relief="flat", cursor="hand2", pady=10
        )
        self.start_btn.pack(pady=40, fill="x")

    # -------------------------------------------------------------
    def start_test(self):
        self.start_btn.config(state="disabled", text="Test çalışıyor...")
        self.ping_gauge.start_measuring()
        self.download_gauge.start_measuring()
        self.upload_gauge.start_measuring()
        self.status_var.set("En yakın sunucu aranıyor...")

        threading.Thread(target=self._run_test, daemon=True).start()

    def _run_test(self):
        try:
            st = speedtest.Speedtest()
            st.get_best_server()

            self.after(0, lambda: self.status_var.set("Ping ölçülüyor..."))
            ping = st.results.ping
            self.after(0, lambda: self.ping_gauge.set_result(ping))

            self.after(0, lambda: self.status_var.set("İndirme hızı ölçülüyor... (biraz sürebilir)"))
            download_bps = st.download()
            download_mbps = download_bps / 1_000_000
            self.after(0, lambda: self.download_gauge.set_result(download_mbps))

            self.after(0, lambda: self.status_var.set("Yükleme hızı ölçülüyor... (biraz sürebilir)"))
            upload_bps = st.upload()
            upload_mbps = upload_bps / 1_000_000
            self.after(0, lambda: self.upload_gauge.set_result(upload_mbps))

            self.after(0, lambda: self.status_var.set("✔ Test tamamlandı"))
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"Hata: İnternet bağlantını kontrol et ({e})"))
            self.after(0, lambda: self.ping_gauge.set_result(0))
            self.after(0, lambda: self.download_gauge.set_result(0))
            self.after(0, lambda: self.upload_gauge.set_result(0))
        finally:
            self.after(0, lambda: self.start_btn.config(state="normal", text="▶ Testi Tekrarla"))