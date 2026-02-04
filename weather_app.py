"""Weather app for Badge.

Displays current weather conditions using wttr.in service.
Shows temperature, conditions, and simple forecast.
"""

import sys
if "core" not in sys.path: sys.path.append("core")
from core import app
import lvgl as lv
import os
import time

class WeatherApp(app.App):
    def __init__(self):
        super().__init__("Weather")
        self.screen = None
        self.location = "Boston"  # Default location
        self.weather_label = None
        self.status_label = None
        self.loading = False

    def run_command(self, cmd):
        """Execute shell command and return output."""
        try:
            tmp_file = "/tmp/weather_cmd.out"
            result = os.system(f"{cmd} > {tmp_file} 2>&1")
            output = ""
            try:
                with open(tmp_file, 'r') as f:
                    output = f.read()
            except:
                pass
            return (result == 0, output)
        except Exception as e:
            return (False, str(e))

    def enter(self, on_exit=None):
        self.on_exit = on_exit

        self.screen = lv.obj()
        self.screen.set_style_bg_color(lv.color_white(), 0)
        lv.screen_load(self.screen)

        # Title
        title = lv.label(self.screen)
        title.set_text("Weather")
        title.set_style_text_color(lv.color_black(), 0)
        title.align(lv.ALIGN.TOP_MID, 0, 5)
        try:
            title.set_style_text_font(lv.font_montserrat_18, 0)
        except:
            pass

        # Weather display area
        self.weather_label = lv.label(self.screen)
        self.weather_label.set_width(380)
        self.weather_label.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.weather_label.set_style_text_color(lv.color_black(), 0)
        try:
            self.weather_label.set_long_mode(lv.LABEL_LONG.WRAP)
        except:
            pass
        self.weather_label.align(lv.ALIGN.CENTER, 0, -10)
        try:
            self.weather_label.set_style_text_font(lv.font_montserrat_14, 0)
        except:
            pass

        # Status label
        self.status_label = lv.label(self.screen)
        self.status_label.set_width(380)
        self.status_label.set_style_text_align(lv.TEXT_ALIGN.CENTER, 0)
        self.status_label.set_style_text_color(lv.color_black(), 0)
        self.status_label.align(lv.ALIGN.BOTTOM_MID, 0, -5)
        try:
            self.status_label.set_style_text_font(lv.font_montserrat_12, 0)
        except:
            pass
        self.status_label.set_text("R: Refresh | ESC: Exit")

        # Setup input
        import input
        if input.driver and input.driver.group:
            input.driver.group.remove_all_objs()
            input.driver.group.add_obj(self.screen)
            lv.group_focus_obj(self.screen)

        self.screen.add_event_cb(self.on_key, lv.EVENT.KEY, None)

        # Fetch weather on start
        self.weather_label.set_text("Loading weather...")
        lv.refr_now(None)
        lv.async_call(lambda _: self.fetch_weather(), None)

    def fetch_weather(self):
        """Fetch weather data from wttr.in."""
        if self.loading:
            return
        self.loading = True

        self.weather_label.set_text("Fetching weather...")
        lv.refr_now(None)

        # Use wttr.in plain text format optimized for terminal
        # Format: ?format=3 gives simple "Location: Conditions, Temp"
        url = f"https://wttr.in/{self.location}?format=3"
        success, output = self.run_command(f"curl -s --max-time 5 '{url}'")

        if not success or not output.strip():
            self.weather_label.set_text(f"Failed to fetch weather\nfor {self.location}\n\nCheck network connection")
            self.loading = False
            return

        # Parse the output
        try:
            # wttr.in format=3 returns: "Location: ☁️  +15°C"
            weather_text = output.strip()

            # Get more detailed info with format=4 (adds wind and visibility)
            url_detail = f"https://wttr.in/{self.location}?format=%l:+%C+%t+%w+%h"
            success, detail = self.run_command(f"curl -s --max-time 5 '{url_detail}'")

            if success and detail.strip():
                # Format: Location: Conditions Temp Wind Humidity
                parts = detail.strip().split(": ", 1)
                if len(parts) == 2:
                    location_name = parts[0]
                    conditions = parts[1]

                    # Format nicely for display
                    display_text = f"{location_name}\n\n{conditions}"
                    self.weather_label.set_text(display_text)
                else:
                    self.weather_label.set_text(weather_text)
            else:
                self.weather_label.set_text(weather_text)

            self.loading = False

        except Exception as e:
            self.weather_label.set_text(f"Error parsing weather:\n{str(e)}")
            self.loading = False

    def on_key(self, e):
        if self.loading:
            return

        key = e.get_key()

        if key == lv.KEY.ESC:
            self.exit()
            if self.on_exit:
                self.on_exit()
        elif key == ord('r') or key == ord('R'):
            # Refresh weather
            lv.async_call(lambda _: self.fetch_weather(), None)

    def exit(self):
        if self.screen:
            self.screen.delete()
            self.screen = None
