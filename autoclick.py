import pyautogui
import gi
import time
import threading
from pynput import mouse
import os

gi.require_version("Gtk", "3.0") # Changed to GTK3
from gi.repository import Gtk, GLib, Gdk # Adw (Adwaita) is primarily GTK4, so removed

# PyAutoGUI ayarları
pyautogui.FAILSAFE = True  # Fareyi sol üst köşeye götürerek script'i durdur

class AutoClickerGtkApp(Gtk.Application): # Gtk.Application can be used directly for Gtk3
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

        self.clicking = False
        self.waiting_for_click = False
        self.click_position = None
        self.click_count = 0
        self.total_clicks = 0
        self.click_interval = 0.1  # Default to 100ms

        self.mouse_listener = None
        self.click_thread = None

    def on_activate(self, app):
        if not hasattr(self, 'window'): # Prevent multiple windows if activate is called again
            self.build_ui(app)

    def build_ui(self, app):
        self.window = Gtk.ApplicationWindow(application=app, title="Otomatik Tıklayıcı")
        self.window.set_default_size(350, 300)
        self.window.set_resizable(False)

        # Main box to hold all content vertically
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        self.window.add(main_box) # In GTK3, add() is used for the single child of a window

        # Header Bar (Gtk.HeaderBar is available in GTK3)
        header_bar = Gtk.HeaderBar()
        self.window.set_titlebar(header_bar)
        header_bar.set_title("Otomatik Tıklayıcı") # GTK3 HeaderBar uses set_title directly

        # Interval Input
        interval_label = Gtk.Label(label="Tıklama Aralığı (ms):")
        self.interval_entry = Gtk.Entry()
        self.interval_entry.set_text("100")
        self.interval_entry.set_width_chars(10) # Set a fixed width
        self.interval_entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
        self.interval_entry.connect("changed", self.on_interval_changed)

        interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        interval_box.pack_start(interval_label, False, False, 0)
        interval_box.pack_start(self.interval_entry, True, True, 0)
        main_box.pack_start(interval_box, False, False, 0) # Pack into main box

        # Total Clicks Input
        total_clicks_label = Gtk.Label(label="Toplam Tıklama Sayısı (0=Sınırsız):")
        self.total_clicks_entry = Gtk.Entry()
        self.total_clicks_entry.set_text("100")
        self.total_clicks_entry.set_width_chars(10) # Set a fixed width
        self.total_clicks_entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
        self.total_clicks_entry.connect("changed", self.on_total_clicks_changed)

        total_clicks_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        total_clicks_box.pack_start(total_clicks_label, False, False, 0)
        total_clicks_box.pack_start(self.total_clicks_entry, True, True, 0)
        main_box.pack_start(total_clicks_box, False, False, 0) # Pack into main box

        # Status Label
        self.status_label = Gtk.Label(label="Durum: Kapalı (ğış)")
        self.status_label.set_margin_top(10)
        self.status_label.set_margin_bottom(10)
        self.status_label.get_style_context().add_class("error-label") # Custom CSS class for GTK3
        main_box.pack_start(self.status_label, False, False, 0)

        # Progress Label
        self.progress_label = Gtk.Label(label="Tıklama: 0 / 0")
        self.progress_label.set_margin_bottom(5)
        main_box.pack_start(self.progress_label, False, False, 0)

        # Progress Bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        main_box.pack_start(self.progress_bar, False, False, 0)

        # Start/Stop Button
        self.start_button = Gtk.Button.new_with_label("Çoklu Tıklamayı Aç")
        self.start_button.set_margin_top(15)
        self.start_button.connect("clicked", self.on_start_button_clicked)
        main_box.pack_start(self.start_button, False, False, 0)

        # CSS for status label (simulating Tkinter's fg="red")
        css_provider = Gtk.CssProvider()
        # GTK3 uses "screen" for providers, not "display"
        css_provider.load_from_data(b"""
            .error-label {
                color: red;
            }
            .success-label {
                color: green;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.window.show_all() # show_all() for GTK3

    def on_interval_changed(self, entry):
        try:
            interval_ms = int(entry.get_text())
            if interval_ms > 0:
                self.click_interval = interval_ms / 1000.0  # Convert ms to seconds
            else:
                self.click_interval = 0.1 # Default if invalid
        except ValueError:
            self.click_interval = 0.1 # Default if not a number

    def on_total_clicks_changed(self, entry):
        try:
            self.total_clicks = int(entry.get_text())
        except ValueError:
            self.total_clicks = 100

    def on_start_button_clicked(self, button):
        if not self.clicking and not self.waiting_for_click:
            self.start_waiting()
        else:
            self.stop_clicking()

    def start_waiting(self):
        self.waiting_for_click = True
        self.status_label.set_label("Durum: Konum Bekleniyor... (şğü)")
        self.status_label.get_style_context().remove_class("error-label")
        self.status_label.get_style_context().add_class("success-label") # Green color
        self.start_button.set_label("Durdur") # Change button text
        self.start_button.set_sensitive(False) # Disable button while waiting for click

        # Start mouse listener to get the click position
        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.mouse_listener.start()

    def on_mouse_click(self, x, y, button, pressed):
        if pressed and self.waiting_for_click:
            self.click_position = (x, y)
            self.waiting_for_click = False
            self.mouse_listener.stop() # Stop listening after getting position
            self.mouse_listener = None # Clear the listener

            GLib.idle_add(self.start_clicking_gui_update) # Update GUI from main thread
            return False # Stop listener

    def start_clicking_gui_update(self):
        # This function is called in the main GTK thread after a click is detected
        self.clicking = True
        self.click_count = 0
        self.status_label.set_label(f"Durum: Tıklıyor (Konum: {self.click_position[0]}, {self.click_position[1]})")
        self.status_label.get_style_context().add_class("success-label")
        self.status_label.get_style_context().remove_class("error-label")
        self.start_button.set_label("Durdur")
        self.start_button.set_sensitive(True) # Re-enable button

        # Start the auto-click thread
        self.click_thread = threading.Thread(target=self.auto_click)
        self.click_thread.daemon = True # Allow program to exit even if thread is running
        self.click_thread.start()

        # Initial progress bar update
        self.update_progress_gui_update()

    def stop_clicking(self):
        self.clicking = False
        self.waiting_for_click = False
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        self.start_button.set_label("Çoklu Tıklamayı Aç")
        self.start_button.set_sensitive(True)
        self.status_label.set_label("Durum: Kapalı (ğış)")
        self.status_label.get_style_context().remove_class("success-label")
        self.status_label.get_style_context().add_class("error-label")
        self.progress_bar.set_fraction(0.0) # Reset progress bar
        self.progress_label.set_label("Tıklama: 0 / 0")


    def auto_click(self):
        while self.clicking:
            if self.total_clicks > 0 and self.click_count >= self.total_clicks:
                self.clicking = False
                GLib.idle_add(self.stop_clicking) # Update GUI from main thread
                break

            if self.click_position: # Only click if position is set
                pyautogui.click(self.click_position[0], self.click_position[1])
                self.click_count += 1
                GLib.idle_add(self.update_progress_gui_update) # Update GUI from main thread

            time.sleep(self.click_interval)

    def update_progress_gui_update(self):
        # This function is called in the main GTK thread to update UI
        if self.total_clicks > 0:
            self.progress_label.set_label(f"Tıklama: {self.click_count} / {self.total_clicks}")
            progress = (self.click_count / self.total_clicks)
            self.progress_bar.set_fraction(progress)
        else:
            self.progress_label.set_label(f"Tıklama: {self.click_count} / Sınırsız (üği)")
            # For unlimited clicks, animate the progress bar
            current_fraction = self.progress_bar.get_fraction()
            new_fraction = (current_fraction + 0.1) % 1.0
            self.progress_bar.set_fraction(new_fraction)


if __name__ == "__main__":
    app = AutoClickerGtkApp(application_id="org.example.autoclicker.gtk3")
    app.run(None)