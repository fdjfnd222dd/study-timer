# Study Timer

**A tiny desktop countdown for studying in time chunks, with automatic breaks.**

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Python 3](https://img.shields.io/badge/python-3-blue)
![Linux](https://img.shields.io/badge/platform-Linux-lightgrey)

Pick a study length, press Start, and work. When the chunk ends you get a
desktop notification and a break starts on its own, then the next chunk, until
you press Stop. It is one small window with no account, no network access and
no background service.

## Features

- Presets for **30 min**, **45 min** and **1 hr**, or type any length from 1 to 600 minutes
- Adjustable break length (default 5 minutes)
- **Start / Pause / Resume, Stop and Reset**
- Breaks and the next study chunk start automatically
- Counter of study chunks completed
- Time in the window title, so it shows on the taskbar when minimized
- Light, dark or system theme
- Accurate over long runs: it counts against a clock deadline instead of adding up ticks

| Button | What it does |
|---|---|
| Start / Pause / Resume | Starts the chunk, freezes it, or continues where it stopped |
| Stop | Ends the session and returns to a fresh study chunk (the counter is kept) |
| Reset | Restarts the current chunk or break from its full length |

Length settings are locked while the timer is running; press Stop to change them.

## Install and run

Needs Python 3 with GTK 4 bindings.

```bash
# Arch / EndeavourOS
sudo pacman -S python-gobject gtk4
# Debian / Ubuntu
sudo apt install python3-gi gir1.2-gtk-4.0

git clone https://github.com/fdjfnd222dd/study-timer.git
cd study-timer
python3 study_timer.py
```

Notifications use `notify-send` if it is installed and are skipped silently if not.

## Files

| File | Purpose |
|---|---|
| `study_timer.py` | The GTK window |
| `timer_core.py` | Timer logic with no GUI, so it can be tested |
| `tests/test_core.py` | Unit tests for the logic |

## Tests

```bash
python3 -m unittest discover -s tests
```

## License

MIT, see [LICENSE](LICENSE).
