# KlippyGram

**KlippyGram** is a Telegram bot to monitor and control your 3D printer via the [Moonraker API](https://moonraker.readthedocs.io/en/latest/) (Klipper).  
Get live status, pause/resume prints, view webcam snapshots, trigger macros, and more—right from Telegram!

---

## ✨ Features

- 📊 View printer status and progress (`/status`)
- ⏸️ Pause, ▶️ resume, and 🛑 stop prints (`/pause`, `/resume`, `/stop`)
- 🚨 Emergency stop (`/emergency_stop`)
- 🌡️ Show temperature info (`/temp`)
- 📸 View webcam snapshot (`/snapshot`)
- 🛠️ Run macros and gcode scripts (`/macros`, `/exec`)
- ...and more!

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/KlippyGram.git
cd KlippyGram
```

### 2. Install dependencies

```bash
pip install python-telegram-bot requests
```

Or, for best practice, use a Python virtual environment:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
pip install python-telegram-bot requests
```

### 3. Configure the bot

Edit `KlippyGram.py` and set these variables at the top:

```python
MOONRAKER_URL = "http://<YOUR-MOONRAKER-IP>"
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
WEBCAM_URL = "http://<YOUR-MOONRAKER-IP>/webcam/?action=snapshot"
```

Get a Telegram bot token from [@BotFather](https://t.me/BotFather).

### 4. Run the bot

```bash
python KlippyGram.py
```

### 5. Use via Telegram

- Search for your bot in Telegram and start a chat.
- Type `/help` to see available commands.

---

## ⚙️ Available Commands

- `/status` — Show print status info (progress, speed, etc.)
- `/emergency_stop` — Emergency stop (motors off)
- `/pause` — Pause the print
- `/resume` — Resume a paused print
- `/stop` — Cancel/stop the print
- `/restart` — Restart Klipper firmware
- `/temp` — Show temperature data (hotend, bed)
- `/snapshot` — Send latest webcam snapshot
- `/help` — Show help message
- `/home` — Home all axes
- `/info` — Printer/firmware details
- `/macros` — List all Klipper macros
- `/job` — Show current print job details
- `/exec` — Run any macro, e.g. `/exec PARK`
- `/more` — Show more commands

---

## 📝 License

MIT License.  
See [LICENSE](LICENSE).

---

**Contributions welcome!**  
Feel free to open issues, suggest features, or submit pull requests.
