"""
Sistem Paneli (Dashboard)
--------------------------
Uygulama açıldığında ilk gösterilen ekran.
CPU / RAM / Disk kullanımını ve donanım sıcaklıklarını canlı olarak gösterir.

Gereken kütüphane: psutil  ->  pip install psutil
Sıcaklık için (opsiyonel, Windows): wmi  ->  pip install wmi
Sıcaklık okuyabilmek için ayrıca bilgisayarında OpenHardwareMonitor ya da
LibreHardwareMonitor'ın ARKA PLANDA ÇALIŞIYOR olması gerekir, çünkü Windows
donanım sıcaklığını doğrudan vermez; bu programlar okuyup bir WMI arayüzünden
paylaşır, biz de oradan okuruz.
"""

import tkinter as tk
import platform
import time
import threading

from modules import style as S

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False

IS_WINDOWS = platform.system() == "Windows"


class Gauge(tk.Canvas):
    """Basit, animasyonlu dairesel yüzde göstergesi."""

    def __init__(self, parent, label, size=140, color=S.ACCENT):
        super().__init__(parent, width=size, height=size, bg=S.BG, highlightthickness=0)
        self.size = size
        self.color = color
        self.label = label
        self.current_value = 0.0   # ekranda görünen (yumuşak geçişli) değer
        self.target_value = 0.0    # gerçek/hedef değer
        self._draw(0)

    def set_value(self, value):
        self.target_value = max(0, min(100, value))

    def animate_step(self):
        """Değeri hedefe doğru yumuşakça kaydırır (basit easing)."""
        diff = self.target_value - self.current_value
        if abs(diff) < 0.3:
            self.current_value = self.target_value
        else:
            self.current_value += diff * 0.15
        self._draw(self.current_value)

    def _draw(self, value):
        self.delete("all")
        pad = 10
        x0, y0 = pad, pad
        x1, y1 = self.size - pad, self.size - pad

        # Arka plan halkası
        self.create_oval(x0, y0, x1, y1, outline=S.CARD_LIGHT, width=10)

        # Değer halkası (0-360 derece, saat 12 yönünden başlar)
        extent = -3.6 * value
        if value > 0:
            self.create_arc(
                x0, y0, x1, y1, start=90, extent=extent,
                style="arc", outline=self.color, width=10
            )

        # Ortadaki yazı
        self.create_text(
            self.size / 2, self.size / 2 - 8,
            text=f"{value:.0f}%", fill=S.TEXT, font=S.FONT_BIG_NUMBER
        )
        self.create_text(
            self.size / 2, self.size / 2 + 22,
            text=self.label, fill=S.TEXT_MUTED, font=S.FONT_SMALL
        )


class DashboardFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=S.BG)
        self._running = True

        tk.Label(
            self, text="📊 Sistem Paneli", bg=S.BG, fg=S.TEXT, font=S.FONT_TITLE
        ).pack(anchor="w", pady=(0, 5))

        if not PSUTIL_OK:
            tk.Label(
                self, text="⚠ 'psutil' kütüphanesi bulunamadı. Kurmak için: pip install psutil",
                bg=S.BG, fg=S.WARNING, font=S.FONT_NORMAL
            ).pack(anchor="w", pady=10)
            return

        # Sistem bilgisi satırı
        info_text = f"{platform.system()} {platform.release()}  •  {platform.processor() or platform.machine()}"
        tk.Label(
            self, text=info_text, bg=S.BG, fg=S.TEXT_MUTED, font=S.FONT_NORMAL
        ).pack(anchor="w", pady=(0, 20))

        # --- Gauge'lar (CPU / RAM / Disk) ---
        gauges_frame = tk.Frame(self, bg=S.BG)
        gauges_frame.pack(pady=10)

        self.cpu_gauge = Gauge(gauges_frame, "CPU", color=S.ACCENT)
        self.cpu_gauge.grid(row=0, column=0, padx=25)

        self.ram_gauge = Gauge(gauges_frame, "RAM", color=S.SUCCESS)
        self.ram_gauge.grid(row=0, column=1, padx=25)

        self.disk_gauge = Gauge(gauges_frame, "Disk (C:)", color=S.WARNING)
        self.disk_gauge.grid(row=0, column=2, padx=25)

        # --- Alt bilgi kartları ---
        cards_frame = tk.Frame(self, bg=S.BG)
        cards_frame.pack(fill="x", pady=25)

        self.temp_card = self._make_card(cards_frame, "🌡 Sıcaklık", "Okunuyor...")
        self.temp_card[0].pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.uptime_card = self._make_card(cards_frame, "⏱ Çalışma Süresi", "Okunuyor...")
        self.uptime_card[0].pack(side="left", fill="both", expand=True, padx=(10, 0))

        self.after(300, self._update_loop)
        self.after(16, self._animation_loop)

    def _make_card(self, parent, title, value):
        card = tk.Frame(parent, bg=S.CARD, padx=20, pady=15)
        tk.Label(card, text=title, bg=S.CARD, fg=S.TEXT_MUTED, font=S.FONT_SUBTITLE).pack(anchor="w")
        value_var = tk.StringVar(value=value)
        tk.Label(card, textvariable=value_var, bg=S.CARD, fg=S.TEXT, font=("Segoe UI", 13)).pack(anchor="w", pady=(5, 0))
        return card, value_var

    # -------------------------------------------------------------
    def _animation_loop(self):
        """Gauge'ları yumuşak geçişle her karede günceller (~60fps)."""
        if not self._running:
            return
        self.cpu_gauge.animate_step()
        self.ram_gauge.animate_step()
        self.disk_gauge.animate_step()
        self.after(16, self._animation_loop)

    def _update_loop(self):
        """Gerçek verileri arka planda toplayıp arayüze işler (1 saniyede bir)."""
        if not self._running:
            return
        threading.Thread(target=self._collect_and_apply, daemon=True).start()
        self.after(1500, self._update_loop)

    def _collect_and_apply(self):
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory().percent
            disk_path = "C:\\" if IS_WINDOWS else "/"
            disk = psutil.disk_usage(disk_path).percent

            boot_time = psutil.boot_time()
            uptime_seconds = int(time.time() - boot_time)
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            uptime_str = f"{hours} saat {minutes} dakika"

            temp_str = self._read_temperature()

            self.after(0, lambda: self._apply_values(cpu, ram, disk, temp_str, uptime_str))
        except Exception as e:
            pass  # sessiz geç, bir sonraki döngüde tekrar dener

    def _apply_values(self, cpu, ram, disk, temp_str, uptime_str):
        self.cpu_gauge.set_value(cpu)
        self.ram_gauge.set_value(ram)
        self.disk_gauge.set_value(disk)
        self.temp_card[1].set(temp_str)
        self.uptime_card[1].set(uptime_str)

    def _read_temperature(self):
        # 1. Yöntem: psutil (Linux/Mac'te çalışır, Windows'ta genelde desteklenmez)
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        return f"{entries[0].current:.0f}°C ({name})"
        except (AttributeError, Exception):
            pass

        # 2. Yöntem: Windows'ta OpenHardwareMonitor/LibreHardwareMonitor WMI köprüsü
        if IS_WINDOWS:
            try:
                import wmi
                w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                sensors = w.Sensor()
                cpu_temps = [s.Value for s in sensors if s.SensorType == "Temperature" and "CPU" in s.Name]
                if cpu_temps:
                    return f"{cpu_temps[0]:.0f}°C (CPU)"
            except Exception:
                pass
            return "Alınamadı (OpenHardwareMonitor kapalı olabilir)"

        return "Bu sistemde desteklenmiyor"

    def destroy(self):
        self._running = False
        super().destroy()