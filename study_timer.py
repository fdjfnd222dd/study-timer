#!/usr/bin/env python3
"""Study Timer: a small GTK4 countdown for studying in time chunks.

Pick 30 / 45 / 60 minutes (or type your own), press Start. When the chunk
ends, a break starts automatically, then the next chunk, until you Stop.
"""
import subprocess
import sys

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

from timer_core import BREAK, IDLE, PAUSED, RUNNING, STUDY, StudyTimer  # noqa: E402

PRESETS = (30, 45, 60)
CSS = b"""
.clock { font-size: 72px; font-weight: 700; font-family: monospace; }
.phase { font-size: 16px; opacity: 0.7; }
.break .clock { color: #2e9e5b; }
"""


def notify(title, body):
    """Desktop notification; silently skipped if notify-send is missing."""
    try:
        subprocess.Popen(["notify-send", "-a", "Study Timer", title, body])
    except OSError:
        pass


def fmt(seconds):
    s = int(seconds + 0.999)  # round up so 00:00 only shows at the true end
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="io.github.studytimer")
        self.timer = StudyTimer()
        self.theme = "system"

    def do_activate(self):
        css = Gtk.CssProvider()
        css.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.win = Gtk.ApplicationWindow(application=self, title="Study Timer")
        self.win.set_default_size(360, 330)
        self.win.set_resizable(False)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        for side in ("top", "bottom", "start", "end"):
            getattr(box, f"set_margin_{side}")(16)
        self.win.set_child(box)

        self.phase_lbl = Gtk.Label(label="Ready", css_classes=["phase"])
        self.clock_lbl = Gtk.Label(label=fmt(self.timer.remaining), css_classes=["clock"])
        self.count_lbl = Gtk.Label(label="Chunks done: 0", css_classes=["phase"])
        box.append(self.phase_lbl)
        box.append(self.clock_lbl)
        box.append(self.count_lbl)

        # Length picker: presets + typed minutes + break minutes.
        row = Gtk.Box(spacing=6, halign=Gtk.Align.CENTER)
        self.preset_btns = []
        for m in PRESETS:
            b = Gtk.Button(label=f"{m if m < 60 else 1} {'min' if m < 60 else 'hr'}")
            b.connect("clicked", lambda _b, m=m: self.set_study(m))
            row.append(b)
            self.preset_btns.append(b)
        box.append(row)

        row2 = Gtk.Box(spacing=6, halign=Gtk.Align.CENTER)
        self.study_spin = Gtk.SpinButton.new_with_range(1, 600, 1)
        self.study_spin.set_value(30)
        self.break_spin = Gtk.SpinButton.new_with_range(1, 120, 1)
        self.break_spin.set_value(5)
        for w in (self.study_spin, self.break_spin):
            w.connect("value-changed", lambda _w: self.apply_lengths())
        row2.append(Gtk.Label(label="Study"))
        row2.append(self.study_spin)
        row2.append(Gtk.Label(label="Break"))
        row2.append(self.break_spin)
        row2.append(Gtk.Label(label="min"))
        box.append(row2)

        # Controls.
        ctl = Gtk.Box(spacing=6, halign=Gtk.Align.CENTER)
        self.go_btn = Gtk.Button(label="Start", css_classes=["suggested-action"])
        self.go_btn.connect("clicked", self.on_go)
        stop = Gtk.Button(label="Stop")
        stop.connect("clicked", self.on_stop)
        reset = Gtk.Button(label="Reset")
        reset.connect("clicked", self.on_reset)
        self.theme_btn = Gtk.Button(label="Theme: system")
        self.theme_btn.connect("clicked", self.on_theme)
        for w in (self.go_btn, stop, reset):
            ctl.append(w)
        box.append(ctl)
        box.append(self.theme_btn)

        GLib.timeout_add(250, self.on_tick)
        self.refresh()
        self.win.present()

    # --- actions -----------------------------------------------------
    def apply_lengths(self):
        if self.timer.state == IDLE:
            self.timer.configure(int(self.study_spin.get_value()) * 60,
                                 int(self.break_spin.get_value()) * 60)
            self.refresh()

    def set_study(self, minutes):
        if self.timer.state == IDLE:
            self.study_spin.set_value(minutes)  # triggers apply_lengths

    def on_go(self, _b):
        if self.timer.state == RUNNING:
            self.timer.pause()
        else:
            self.timer.start()
        self.refresh()

    def on_stop(self, _b):
        self.timer.stop()
        self.refresh()

    def on_reset(self, _b):
        self.timer.reset()
        self.refresh()

    def on_theme(self, _b):
        self.theme = {"system": "light", "light": "dark", "dark": "system"}[self.theme]
        settings = Gtk.Settings.get_default()
        if self.theme == "system":
            settings.reset_property("gtk-application-prefer-dark-theme")
        else:
            settings.set_property("gtk-application-prefer-dark-theme", self.theme == "dark")
        self.theme_btn.set_label(f"Theme: {self.theme}")

    def on_tick(self):
        done = self.timer.tick()
        if done == STUDY:
            notify("Study chunk done", "Break time.")
        elif done == BREAK:
            notify("Break over", "Back to studying.")
        self.refresh()
        return True

    # --- display -----------------------------------------------------
    def refresh(self):
        t = self.timer
        self.clock_lbl.set_label(fmt(t.remaining))
        name = "Break" if t.phase == BREAK else "Study"
        status = {IDLE: "Ready", RUNNING: name, PAUSED: f"{name} (paused)"}[t.state]
        self.phase_lbl.set_label(status)
        self.count_lbl.set_label(f"Chunks done: {t.sessions}")
        self.go_btn.set_label({IDLE: "Start", RUNNING: "Pause", PAUSED: "Resume"}[t.state])
        # Window title mirrors the time so it shows on the taskbar when minimized.
        self.win.set_title(f"{fmt(t.remaining)} {name}" if t.state != IDLE else "Study Timer")
        idle = t.state == IDLE
        for w in (self.study_spin, self.break_spin, *self.preset_btns):
            w.set_sensitive(idle)
        (self.clock_lbl.get_parent()).remove_css_class("break")
        if t.phase == BREAK:
            self.clock_lbl.get_parent().add_css_class("break")


if __name__ == "__main__":
    sys.exit(App().run(None))
