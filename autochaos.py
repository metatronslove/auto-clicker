import pyautogui
import gi
gi.require_version('Gtk', '3.0')
import time
import threading
from pynput import mouse, keyboard
import os
import json
from gi.repository import Gtk, GLib, Gdk, cairo

# PyAutoGUI settings
pyautogui.FAILSAFE = True

class CellRendererSwatch(Gtk.CellRenderer):
	"""Custom cell renderer for color swatches."""
	def __init__(self):
		super().__init__()
		self.set_property("width", 20)
		self.set_property("height", 20)
		self.r = 0
		self.g = 0
		self.b = 0

	def do_render(self, cr, widget, background_area, cell_area, flags):
		"""Render the color swatch."""
		cr.set_source_rgb(self.r / 255.0, self.g / 255.0, self.b / 255.0)
		cr.rectangle(cell_area.x, cell_area.y, cell_area.width, cell_area.height)
		cr.fill()
		cr.set_source_rgb(0, 0, 0)  # Black border
		cr.set_line_width(1)
		cr.rectangle(cell_area.x, cell_area.y, cell_area.width, cell_area.height)
		cr.stroke()

	def do_get_size(self, widget, cell_area):
		"""Return the size of the swatch."""
		return (0, 0, 20, 20)

class AutoClickerGtkApp(Gtk.Application):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.connect('activate', self.on_activate)

		# Initialize variables
		self.clicking = False
		self.waiting_for_click = False
		self.waiting_for_color_pick = False
		self.click_position = None
		self.click_count = 0
		self.total_clicks = 0
		self.click_interval = 0.1
		self.color_detection_enabled = False
		self.color_delay = 1.5
		self.selected_colors = []
		self.mouse_listener = None
		self.click_thread = None
		self.keyboard_listener = None

		# Load settings from JSON
		self.load_settings()

		# Start keyboard listener for emergency stop
		self.start_keyboard_listener()

	def load_settings(self):
		"""Load settings from autoclick.json or set defaults."""
		default_settings = {
			'click_interval_ms': 100,
			'total_clicks': 100,
			'color_detection_enabled': False,
			'color_delay_ms': 1500,
			'selected_colors': []
		}
		try:
			if os.path.exists('autoclick.json'):
				with open('autoclick.json', 'r') as f:
					settings = json.load(f)
					self.click_interval = settings.get('click_interval_ms', default_settings['click_interval_ms']) / 1000.0
					self.total_clicks = settings.get('total_clicks', default_settings['total_clicks'])
					self.color_detection_enabled = settings.get('color_detection_enabled', default_settings['color_detection_enabled'])
					self.color_delay = settings.get('color_delay_ms', default_settings['color_delay_ms']) / 1000.0
					colors = settings.get('selected_colors', default_settings['selected_colors'])
					self.selected_colors = [tuple(color) for color in colors if isinstance(color, list) and len(color) == 3]
					print(f"Loaded settings: {settings}")
					print(f"click_interval: {self.click_interval}s, color_delay: {self.color_delay}s")
			else:
				print("No autoclick.json found, using defaults")
				self.click_interval = default_settings['click_interval_ms'] / 1000.0
				self.total_clicks = default_settings['total_clicks']
				self.color_detection_enabled = default_settings['color_detection_enabled']
				self.color_delay = default_settings['color_delay_ms'] / 1000.0
				self.selected_colors = default_settings['selected_colors']
				self.save_settings()
		except json.JSONDecodeError as e:
			print(f"Error decoding autoclick.json: {e}")
			self.apply_default_settings(default_settings)
		except Exception as e:
			print(f"Error loading settings: {e}")
			self.apply_default_settings(default_settings)

	def apply_default_settings(self, default_settings):
		"""Apply default settings and save them."""
		self.click_interval = default_settings['click_interval_ms'] / 1000.0
		self.total_clicks = default_settings['total_clicks']
		self.color_detection_enabled = default_settings['color_detection_enabled']
		self.color_delay = default_settings['color_delay_ms'] / 1000.0
		self.selected_colors = default_settings['selected_colors']
		self.save_settings()

	def save_settings(self):
		"""Save current settings to autoclick.json."""
		settings = {
			'click_interval_ms': int(self.click_interval * 1000),
			'total_clicks': self.total_clicks,
			'color_detection_enabled': self.color_detection_enabled,
			'color_delay_ms': int(self.color_delay * 1000),
			'selected_colors': [list(color) for color in self.selected_colors]
		}
		try:
			with open('autoclick.json', 'w') as f:
				json.dump(settings, f, indent=4)
			print(f"Saved settings: {settings}")
		except Exception as e:
			print(f"Error saving settings: {e}")

	def start_keyboard_listener(self):
		"""Start pynput keyboard listener for Ctrl+Esc."""
		self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
		self.keyboard_listener.start()

	def on_key_press(self, key):
		"""Handle keyboard events for emergency stop."""
		try:
			if key == keyboard.Key.esc and keyboard.Controller().pressed(keyboard.Key.ctrl):
				if self.clicking or self.waiting_for_click or self.waiting_for_color_pick:
					GLib.idle_add(self.stop_waiting)
				return False
		except Exception:
			pass

	def on_activate(self, app):
		if not hasattr(self, 'window'):
			self.build_ui(app)

	def build_ui(self, app):
		self.window = Gtk.ApplicationWindow(application=app, title="🇹🇷 Otomatik Kaos Tıklayıcı")
		self.window.set_default_size(400, 500)
		self.window.set_resizable(False)

		# Main box
		main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
		main_box.set_margin_top(20)
		main_box.set_margin_bottom(20)
		main_box.set_margin_start(20)
		main_box.set_margin_end(20)
		self.window.add(main_box)

		# Header Bar
		header_bar = Gtk.HeaderBar()
		self.window.set_titlebar(header_bar)
		header_bar.set_title("🇹🇷 Otomatik Kaos Tıklayıcı")

		# Interval Input
		interval_label = Gtk.Label(label="Tıklama Aralığı (ms):")
		self.interval_entry = Gtk.Entry()
		self.interval_entry.set_text(str(int(self.click_interval * 1000)))
		self.interval_entry.set_width_chars(10)
		self.interval_entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
		self.interval_entry.connect("changed", self.on_interval_changed)

		interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
		interval_box.pack_start(interval_label, False, False, 0)
		interval_box.pack_start(self.interval_entry, True, True, 0)
		main_box.pack_start(interval_box, False, False, 0)

		# Total Clicks Input
		total_clicks_label = Gtk.Label(label="Toplam Tıklama Sayısı (0=Sınırsız):")
		self.total_clicks_entry = Gtk.Entry()
		self.total_clicks_entry.set_text(str(self.total_clicks))
		self.total_clicks_entry.set_width_chars(10)
		self.total_clicks_entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
		self.total_clicks_entry.connect("changed", self.on_total_clicks_changed)

		total_clicks_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
		total_clicks_box.pack_start(total_clicks_label, False, False, 0)
		total_clicks_box.pack_start(self.total_clicks_entry, True, True, 0)
		main_box.pack_start(total_clicks_box, False, False, 0)

		# Color Detection Checkbox
		self.color_detection_check = Gtk.CheckButton(label="Renk Algılama Açık")
		self.color_detection_check.set_active(self.color_detection_enabled)
		self.color_detection_check.connect("toggled", self.on_color_detection_toggled)
		main_box.pack_start(self.color_detection_check, False, False, 0)

		# Color Picker Button
		self.color_picker_button = Gtk.Button.new_with_label("Renk Seç")
		self.color_picker_button.connect("clicked", self.on_color_picker_clicked)
		self.color_picker_button.set_sensitive(self.color_detection_enabled)
		main_box.pack_start(self.color_picker_button, False, False, 0)

		# Color Delay Input
		color_delay_label = Gtk.Label(label="Renk Savuşturma Aralığı (ms):")
		self.color_delay_entry = Gtk.Entry()
		self.color_delay_entry.set_text(str(int(self.color_delay * 1000)))
		self.color_delay_entry.set_width_chars(10)
		self.color_delay_entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
		self.color_delay_entry.connect("changed", self.on_color_delay_changed)

		color_delay_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
		color_delay_box.pack_start(color_delay_label, False, False, 0)
		color_delay_box.pack_start(self.color_delay_entry, True, True, 0)
		main_box.pack_start(color_delay_box, False, False, 0)

		# Selected Colors Box
		self.colors_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
		self.colors_label = Gtk.Label(label="Seçilen Renkler:")
		self.colors_box.pack_start(self.colors_label, False, False, 0)
		self.colors_flowbox = Gtk.FlowBox()
		self.colors_flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
		self.colors_box.pack_start(self.colors_flowbox, False, False, 0)
		colors_edit_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
		self.edit_colors_button = Gtk.Button.new_with_label("Düzenle")
		self.edit_colors_button.connect("clicked", self.on_edit_colors_clicked)
		self.edit_colors_button.set_sensitive(self.color_detection_enabled)
		colors_edit_box.pack_end(self.edit_colors_button, False, False, 0)
		self.colors_box.pack_start(colors_edit_box, False, False, 0)
		main_box.pack_start(self.colors_box, False, False, 0)

		# Status Label
		self.status_label = Gtk.Label(label="Durum: Kapalı (ğış)")
		self.status_label.set_margin_top(10)
		self.status_label.set_margin_bottom(10)
		self.status_label.get_style_context().add_class("error-label")
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
		self.start_button = Gtk.Button.new_with_label("Çoklu Tıklayıcıyı Aç")
		self.start_button.set_margin_top(15)
		self.start_button.connect("clicked", self.on_start_button_clicked)
		main_box.pack_start(self.start_button, False, False, 0)

		# Emergency Stop Label
		emergency_label = Gtk.Label(label="Acil Durdurma: Ctrl+Esc")
		main_box.pack_start(emergency_label, False, False, 0)

		# CSS
		css_provider = Gtk.CssProvider()
		css_provider.load_from_data(b"""
			.error-label {
				color: red;
			}
			.success-label {
				color: green;
			}
			.warning-label {
				color: orange;
			}
			.color-swatch {
				border: 1px solid black;
				margin-right: 5px;
			}
		""")
		Gtk.StyleContext.add_provider_for_screen(
			Gdk.Screen.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
		)

		self.window.show_all()
		self.update_colors_label()

	def on_interval_changed(self, entry):
		try:
			interval_ms = int(entry.get_text())
			if interval_ms > 0:
				self.click_interval = interval_ms / 1000.0
			else:
				self.click_interval = 0.1
		except ValueError:
			self.click_interval = 0.1
		self.save_settings()

	def on_total_clicks_changed(self, entry):
		try:
			self.total_clicks = int(entry.get_text())
		except ValueError:
			self.total_clicks = 100
		self.save_settings()

	def on_color_delay_changed(self, entry):
		try:
			delay_ms = int(entry.get_text())
			if delay_ms > 0:
				self.color_delay = delay_ms / 1000.0
			else:
				self.color_delay = 1.5
		except ValueError:
			self.color_delay = 1.5
		self.save_settings()

	def on_color_detection_toggled(self, checkbutton):
		self.color_detection_enabled = checkbutton.get_active()
		self.color_picker_button.set_sensitive(self.color_detection_enabled)
		self.color_delay_entry.set_sensitive(self.color_detection_enabled)
		self.edit_colors_button.set_sensitive(self.color_detection_enabled)
		self.colors_flowbox.set_sensitive(self.color_detection_enabled)
		self.save_settings()

	def on_color_picker_clicked(self, button):
		self.waiting_for_color_pick = True
		self.status_label.set_label("Durum: Renk Seçimi Bekleniyor...")
		self.status_label.get_style_context().remove_class("error-label")
		self.status_label.get_style_context().remove_class("warning-label")
		self.status_label.get_style_context().add_class("success-label")
		self.color_picker_button.set_sensitive(False)
		self.start_button.set_sensitive(False)
		self.edit_colors_button.set_sensitive(False)

		# Start mouse listener for color picking
		self.mouse_listener = mouse.Listener(on_click=self.on_color_pick_click)
		self.mouse_listener.start()

	def on_edit_colors_clicked(self, button):
		dialog = Gtk.Dialog(title="Renkleri Düzenle", parent=self.window, modal=True)
		dialog.add_button("Kapat", Gtk.ResponseType.CLOSE)
		dialog.set_default_size(300, 200)

		box = dialog.get_content_area()
		box.set_margin_top(10)
		box.set_margin_bottom(10)
		box.set_margin_start(10)
		box.set_margin_end(10)

		# List store for colors (string and RGB values)
		list_store = Gtk.ListStore(str, int, int, int)  # color string, r, g, b
		for r, g, b in self.selected_colors:
			list_store.append([f"RGB({r}, {g}, {b})", r, g, b])

		# Tree view
		tree_view = Gtk.TreeView(model=list_store)

		# Swatch column
		swatch_renderer = CellRendererSwatch()
		swatch_column = Gtk.TreeViewColumn("Renk", swatch_renderer)
		swatch_column.add_attribute(swatch_renderer, "r", 1)
		swatch_column.add_attribute(swatch_renderer, "g", 2)
		swatch_column.add_attribute(swatch_renderer, "b", 3)
		tree_view.append_column(swatch_column)

		# Text column
		text_renderer = Gtk.CellRendererText()
		text_column = Gtk.TreeViewColumn("RGB Kodu", text_renderer, text=0)
		tree_view.append_column(text_column)

		# Scrolled window
		scrolled_window = Gtk.ScrolledWindow()
		scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
		scrolled_window.add(tree_view)
		box.pack_start(scrolled_window, True, True, 0)

		# Remove button
		remove_button = Gtk.Button.new_with_label("Seçili Rengi Kaldır")
		remove_button.connect("clicked", self.on_remove_color_clicked, tree_view, list_store)
		box.pack_start(remove_button, False, False, 5)

		dialog.show_all()
		dialog.run()
		dialog.destroy()

	def on_remove_color_clicked(self, button, tree_view, list_store):
		selection = tree_view.get_selection()
		model, tree_iter = selection.get_selected()
		if tree_iter:
			color_str = model[tree_iter][0]  # e.g., "RGB(255,0,0)"
			rgb = tuple(map(int, color_str[4:-1].split(',')))
			if rgb in self.selected_colors:
				self.selected_colors.remove(rgb)
				self.update_colors_label()
				self.save_settings()
				list_store.remove(tree_iter)

	def on_color_pick_click(self, x, y, button, pressed):
		if pressed and self.waiting_for_color_pick:
			try:
				time.sleep(0.1)
				screen_width, screen_height = pyautogui.size()
				x, y = int(x), int(y)
				if 0 <= x < screen_width and 0 <= y < screen_height:
					color = pyautogui.pixel(x, y)
					print(f"Color picked at ({x}, {y}): RGB({color[0]}, {color[1]}, {color[2]})")
					if color not in self.selected_colors:
						self.selected_colors.append(color)
						self.update_colors_label()
						self.save_settings()
				else:
					print(f"Coordinates out of bounds: ({x}, {y})")
					GLib.idle_add(self.show_color_pick_error, "Tıklama ekran sınırları dışında!")
			except Exception as e:
				print(f"Error picking color: {e}")
				GLib.idle_add(self.show_color_pick_error, f"Renk seçme hatası: {str(e)}")
			finally:
				self.waiting_for_color_pick = False
				self.mouse_listener.stop()
				self.mouse_listener = None
				GLib.idle_add(self.reset_color_picker_gui)
			return False

	def show_color_pick_error(self, message):
		"""Display an error message in the status label."""
		self.status_label.set_label(f"Durum: {message}")
		self.status_label.get_style_context().remove_class("success-label")
		self.status_label.get_style_context().remove_class("error-label")
		self.status_label.get_style_context().add_class("warning-label")

	def reset_color_picker_gui(self):
		self.status_label.set_label("Durum: Kapalı (ğış)" if not self.clicking else
								   f"Durum: Tıklıyor (Konum: {self.click_position[0]}, {self.click_position[1]})")
		self.status_label.get_style_context().add_class("error-label" if not self.clicking else "success-label")
		self.status_label.get_style_context().remove_class("success-label" if not self.clicking else "error-label")
		self.status_label.get_style_context().remove_class("warning-label")
		self.color_picker_button.set_sensitive(self.color_detection_enabled)
		self.start_button.set_sensitive(True)
		self.edit_colors_button.set_sensitive(self.color_detection_enabled)

	def update_colors_label(self):
		"""Update the colors display with swatches only."""
		if not hasattr(self, 'colors_flowbox'):
			return  # Skip if UI not yet built

		# Clear existing children in flowbox
		for child in self.colors_flowbox.get_children():
			self.colors_flowbox.remove(child)

		if self.selected_colors:
			self.colors_label.set_label("Seçilen Renkler:")
			for r, g, b in self.selected_colors:
				hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
				# Create swatch
				swatch = Gtk.DrawingArea()
				swatch.set_size_request(20, 20)
				swatch.connect("draw", self.draw_color_swatch, r, g, b)
				swatch.get_style_context().add_class("color-swatch")
				hbox.pack_start(swatch, False, False, 0)
				self.colors_flowbox.add(hbox)
		else:
			self.colors_label.set_label("Seçilen Renkler: Yok")
		self.colors_flowbox.show_all()

	def draw_color_swatch(self, widget, cr, r, g, b):
		"""Draw a color swatch in the DrawingArea."""
		cr.set_source_rgb(r / 255.0, g / 255.0, b / 255.0)
		cr.paint()
		return False

	def stop_waiting(self):
		self.clicking = False
		self.waiting_for_click = False
		self.waiting_for_color_pick = False
		if self.mouse_listener:
			self.mouse_listener.stop()
			self.mouse_listener = None
		self.start_button.set_label("Çoklu Tıklayıcıyı Aç")
		self.start_button.set_sensitive(True)
		self.color_picker_button.set_sensitive(self.color_detection_enabled)
		self.edit_colors_button.set_sensitive(self.color_detection_enabled)
		self.status_label.set_label("Durum: Kapalı (ğış)")
		self.status_label.get_style_context().remove_class("success-label")
		self.status_label.get_style_context().remove_class("warning-label")
		self.status_label.get_style_context().add_class("error-label")
		self.progress_bar.set_fraction(0.0)
		self.progress_label.set_label("Tıklama: 0 / 0")

	def on_start_button_clicked(self, button):
		if not self.clicking and not self.waiting_for_click and not self.waiting_for_color_pick:
			self.start_waiting()
		else:
			self.stop_waiting()

	def start_waiting(self):
		self.waiting_for_click = True
		self.status_label.set_label("Durum: Konum Bekleniyor... (şğü)")
		self.status_label.get_style_context().remove_class("error-label")
		self.status_label.get_style_context().remove_class("warning-label")
		self.status_label.get_style_context().add_class("success-label")
		self.start_button.set_label("Durdur")
		self.start_button.set_sensitive(False)
		self.color_picker_button.set_sensitive(False)
		self.edit_colors_button.set_sensitive(False)

		self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
		self.mouse_listener.start()

	def on_mouse_click(self, x, y, button, pressed):
		if pressed and self.waiting_for_click:
			self.click_position = (x, y)
			self.waiting_for_click = False
			self.mouse_listener.stop()
			self.mouse_listener = None
			GLib.idle_add(self.start_clicking_gui_update)
			return False

	def start_clicking_gui_update(self):
		self.clicking = True
		self.click_count = 0
		self.status_label.set_label(f"Durum: Tıklıyor (Konum: {self.click_position[0]}, {self.click_position[1]})")
		self.status_label.get_style_context().add_class("success-label")
		self.status_label.get_style_context().remove_class("error-label")
		self.status_label.get_style_context().remove_class("warning-label")
		self.start_button.set_label("Durdur")
		self.start_button.set_sensitive(True)
		self.color_picker_button.set_sensitive(self.color_detection_enabled)
		self.edit_colors_button.set_sensitive(self.color_detection_enabled)

		self.click_thread = threading.Thread(target=self.auto_click)
		self.click_thread.daemon = True
		self.click_thread.start()

		self.update_progress_gui_update()

	def auto_click(self):
		def is_color_similar(pixel, selected_color, tolerance=5):
			"""Check if pixel is within tolerance of selected_color."""
			return all(abs(pixel[i] - selected_color[i]) <= tolerance for i in range(3))

		while self.clicking:
			if self.total_clicks > 0 and self.click_count >= self.total_clicks:
				self.clicking = False
				GLib.idle_add(self.stop_waiting)
				break

			if self.click_position:
				is_color_match = False
				current_interval = self.click_interval
				print(f"Initial: click_interval={self.click_interval}s, color_delay={self.color_delay}s")
				print(f"Selected colors: {self.selected_colors}")
				if self.color_detection_enabled and self.selected_colors:
					try:
						pixel = pyautogui.pixel(self.click_position[0], self.click_position[1])
						print(f"Checked color at ({self.click_position[0]}, {self.click_position[1]}): RGB{pixel}")
						for color in self.selected_colors:
							if is_color_similar(pixel, color):
								is_color_match = True
								current_interval = self.color_delay
								print(f"Color match with {color}, using color_delay: {self.color_delay}s")
								break
							else:
								print(f"No match with {color}, diff: {[abs(pixel[i] - color[i]) for i in range(3)]}")
						if not is_color_match:
							current_interval = self.click_interval
							print(f"No color match, using click_interval: {self.click_interval}s")
					except Exception as e:
						print(f"Error getting pixel color: {e}")
						current_interval = self.click_interval
						print(f"Error case, using click_interval: {self.click_interval}s")
				else:
					print(f"Color detection disabled or no selected colors, using click_interval: {self.click_interval}s")

				# Wait for the determined interval BEFORE clicking
				print(f"Waiting for {current_interval}s")
				time.sleep(current_interval)

				# Perform the click
				pyautogui.click(self.click_position[0], self.click_position[1])
				if is_color_match:
					print(f"Performed color delay click (not counted)")
				else:
					self.click_count += 1
					print(f"Performed regular click (counted: {self.click_count})")
					GLib.idle_add(self.update_progress_gui_update)

	def update_progress_gui_update(self):
		if self.total_clicks > 0:
			self.progress_label.set_label(f"Tıklama: {self.click_count} / {self.total_clicks}")
			progress = (self.click_count / self.total_clicks) if self.total_clicks > 0 else 0.0
			self.progress_bar.set_fraction(progress)
		else:
			self.progress_label.set_label(f"Tıklama: {self.click_count} / Sınırsız (üği)")
			current_fraction = self.progress_bar.get_fraction()
			new_fraction = (current_fraction + 0.1) % 1.0
			self.progress_bar.set_fraction(new_fraction)

if __name__ == "__main__":
	app = AutoClickerGtkApp(application_id="org.example.autoclicker.gtk3")
	app.run(None)