import requests
import io
import html
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
)

# ================== CONFIGURATION ===================
MOONRAKER_URL = "http://<YOUR-MOONRAKER-IP>"  # Your Moonraker API server URL
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Replace with your bot token
CHAT_ID = "YOUR_CHAT_ID"                    # Replace with your Chat ID
WEBCAM_URL = "http://<YOUR-MOONRAKER-IP>/webcam/?action=snapshot"  # Webcam snapshot URL
# ====================================================

def get_printer_status():
    """
    Query Moonraker for printer status information.
    Returns a dict with print progress and stats.
    """
    url = f"{MOONRAKER_URL}/printer/objects/query?print_stats"
    try:
        response = requests.get(url, timeout=4).json()
        stats = response['result']['status']['print_stats']
        return {
            "speed": stats.get("print_speed", 0),
            "flow": stats.get("flow_factor", 1.0),
            "filament_used": stats.get("filament_used", 0),
            "layer": stats.get("info", {}).get("current_layer", 0),
            "total_layers": stats.get("info", {}).get("total_layer", 0),
            "estimated_total_time": stats.get("print_duration", 0),
            "estimated_remaining_time": stats.get("estimated_time", 0),
            "state": stats.get("state", "unknown")
        }
    except Exception as e:
        print(f"Error in get_printer_status: {e}")
        return None

def format_status(status):
    """
    Format printer status dictionary as a Telegram HTML string.
    """
    if not status:
        return "❌ Failed to retrieve printer status."
    return (
        f"🖨️ <b>Printer Status</b>\n"
        f"Speed: {html.escape(str(status['speed']))} mm/s\n"
        f"Flow: {html.escape(str(status['flow']))}\n"
        f"Filament Used: {html.escape(str(round(status['filament_used'], 2)))} mm\n"
        f"Layer: {html.escape(str(status['layer']))}/{html.escape(str(status['total_layers']))}\n"
        f"Total Time: {html.escape(str(round(status['estimated_total_time'] / 60, 2)))} min\n"
        f"Remaining Time: {html.escape(str(round(status['estimated_remaining_time'] / 60, 2)))} min\n"
        f"State: {html.escape(str(status['state']))}\n"
    )

def get_temperature_data():
    """
    Query Moonraker for extruder and bed temperatures.
    """
    url = f"{MOONRAKER_URL}/printer/objects/query?extruder&heater_bed"
    try:
        status = requests.get(url, timeout=4).json()['result']['status']
        extruder = status.get('extruder', {})
        bed = status.get('heater_bed', {})
        return (
            f"🌡️ <b>Temperature Data</b>\n"
            f"Hotend: {html.escape(str(extruder.get('temperature', 'N/A')))}°C / {html.escape(str(extruder.get('target', 'N/A')))}°C\n"
            f"Bed: {html.escape(str(bed.get('temperature', 'N/A')))}°C / {html.escape(str(bed.get('target', 'N/A')))}°C"
        )
    except Exception as e:
        print(f"Error in get_temperature_data: {e}")
        return "❌ Failed to retrieve temperature data."

def moonraker_post(command):
    """
    Post a basic printer command to Moonraker's print API.
    Used for pause, resume, cancel, etc.
    """
    url = f"{MOONRAKER_URL}/printer/print/{command}"
    try:
        response = requests.post(url, timeout=4)
        return response.status_code == 204 or response.status_code == 200
    except Exception as e:
        print(f"Error in moonraker_post: {e}")
        return False

# --- Command Handlers ---
# Each function below is mapped to a Telegram bot command

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current print status."""
    status = get_printer_status()
    await update.message.reply_text(format_status(status), parse_mode='HTML')

async def temp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show temperature data."""
    temp_data = get_temperature_data()
    await update.message.reply_text(temp_data, parse_mode='HTML')

async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pause the print."""
    success = moonraker_post("pause")
    await update.message.reply_text("⏸️ Print paused." if success else "❌ Failed to pause print.")

async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resume the print."""
    success = moonraker_post("resume")
    await update.message.reply_text("▶️ Print resumed." if success else "❌ Failed to resume print.")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel/stop the print."""
    success = moonraker_post("cancel")
    await update.message.reply_text("🛑 Print cancelled." if success else "❌ Failed to cancel print.")

async def snapshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send webcam snapshot."""
    try:
        response = requests.get(WEBCAM_URL, timeout=8)
        if response.status_code == 200:
            photo_bytes = io.BytesIO(response.content)
            await update.message.reply_photo(photo=photo_bytes, caption="📸 Latest webcam snapshot")
        else:
            await update.message.reply_text("❌ Failed to get webcam snapshot.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def home_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Home all printer axes."""
    url = f"{MOONRAKER_URL}/printer/gcode/script"
    try:
        response = requests.post(url, json={"script": "G28"}, timeout=4)
        if response.status_code in [204, 200]:
            await update.message.reply_text("🏠 Printer homing started (G28).")
        else:
            await update.message.reply_text("❌ Failed to home printer.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart Klipper firmware."""
    url = f"{MOONRAKER_URL}/server/restart"
    try:
        response = requests.post(url, timeout=4)
        if response.status_code in [204, 200]:
            await update.message.reply_text("🔄 Klipper restart triggered.")
        else:
            await update.message.reply_text("❌ Failed to restart Klipper.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def emergency_stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Trigger emergency stop."""
    url = f"{MOONRAKER_URL}/printer/emergency_stop"
    try:
        response = requests.post(url, timeout=4)
        if response.status_code in [204, 200]:
            await update.message.reply_text("⛔ Emergency stop triggered!")
        else:
            await update.message.reply_text("❌ Failed to trigger emergency stop.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show printer/firmware details."""
    url = f"{MOONRAKER_URL}/printer/info"
    try:
        response = requests.get(url, timeout=4).json()
        info = response.get('result', {})
        text = (
            f"<b>Printer Info:</b>\n"
            f"Firmware: {html.escape(str(info.get('config_file', 'N/A')))}\n"
            f"Version: {html.escape(str(info.get('klipper_path', 'N/A')))}\n"
            f"Serial: {html.escape(str(info.get('serial_path', 'N/A')))}"
        )
        await update.message.reply_text(text, parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def macros_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    List macros as clickable inline buttons.
    """
    url = f"{MOONRAKER_URL}/printer/objects/list"
    try:
        response = requests.get(url, timeout=4).json()
        macros = [obj.replace("gcode_macro ", "") for obj in response['result']['objects'] if obj.startswith("gcode_macro ")]
        # Only show user macros (not _internal)
        keyboard = [
            [InlineKeyboardButton(macro, callback_data=f"exec_macro:{macro}")]
            for macro in macros if not macro.startswith('_')
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = "🛠️ <b>Available Macros:</b>\nClick a macro to execute it."
        await update.message.reply_text(text, parse_mode='HTML', reply_markup=reply_markup)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def exec_macro_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback when a macro inline button is clicked.
    """
    query = update.callback_query
    await query.answer()
    macro_name = query.data.split(":", 1)[1]
    url = f"{MOONRAKER_URL}/printer/gcode/script"
    try:
        response = requests.post(url, json={"script": macro_name}, timeout=4)
        if response.status_code in [200, 204]:
            await query.edit_message_text(
                f"✅ Executed: <code>{html.escape(macro_name)}</code>", parse_mode='HTML'
            )
        else:
            await query.edit_message_text(f"❌ Failed to execute macro: {html.escape(macro_name)}")
    except Exception as e:
        await query.edit_message_text(f"❌ Error: {e}")

async def exec_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Run any macro by command: /exec MACRO_NAME [ARGS...]
    """
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ Usage: /exec MACRO_NAME [ARGS...]\nExample: /exec PARK or /exec SET_PAUSE_AT_LAYER 10"
            )
            return
        macro_command = " ".join(context.args)
        url = f"{MOONRAKER_URL}/printer/gcode/script"
        response = requests.post(url, json={"script": macro_command}, timeout=4)
        if response.status_code in [200, 204]:
            await update.message.reply_text(
                f"✅ Executed: <code>{html.escape(macro_command)}</code>",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(f"❌ Failed to execute macro: {html.escape(macro_command)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def job_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show details of the current print job."""
    url = f"{MOONRAKER_URL}/printer/objects/query?print_stats"
    try:
        response = requests.get(url, timeout=4).json()
        stats = response['result']['status']['print_stats']
        filename = stats.get('filename', '')
        state = stats.get('state', '')
        duration = stats.get('print_duration', 0)
        info = stats.get('info', {})
        totallayer = info.get('totallayer', 'N/A')
        currentlayer = info.get('currentlayer', 'N/A')
        text = (
            f"<b>Current Print Job:</b>\n"
            f"State: {html.escape(str(state))}\n"
            f"Filename: {html.escape(str(filename))}\n"
            f"Duration: {html.escape(str(round(duration/60, 1)))} min\n"
            f"Total Layers: {html.escape(str(totallayer))}\n"
            f"Current Layer: {html.escape(str(currentlayer))}"
        )
        await update.message.reply_text(text, parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main commands."""
    commands = (
        "<b>Main Commands:</b>\n"
        "\n"
        "/status — Show print status info (progress, speed, etc.)\n"
        "/emergency_stop — Emergency stop (motors off)\n"
        "/pause — Pause the print\n"
        "/resume — Resume a paused print\n"
        "/stop — Cancel/stop the print\n"
        "/restart — Restart Klipper firmware\n"
        "/temp — Show temperature data (hotend, bed)\n"
        "/snapshot — Send latest webcam snapshot\n"
        "/help — Show this help message\n"
        "/more — Show more commands"
    )
    await update.message.reply_text(commands, parse_mode='HTML')

async def more_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show additional commands."""
    commands = (
        "<b>More Commands:</b>\n"
        "\n"
        "/home — Home all axes\n"
        "/info — Printer/firmware details\n"
        "/macros — List all Klipper macros\n"
        "/job — Show current print job details\n"
        "/exec — Run any macro, e.g. /exec PARK\n"
        "/help — Show this help message\n"
        "/more — Show more commands"
    )
    await update.message.reply_text(commands, parse_mode='HTML')

def main():
    """
    Entry point. Registers command handlers and starts the bot.
    """
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('status', status_command))
    app.add_handler(CommandHandler('emergency_stop', emergency_stop_command))
    app.add_handler(CommandHandler('pause', pause_command))
    app.add_handler(CommandHandler('resume', resume_command))
    app.add_handler(CommandHandler('stop', stop_command))
    app.add_handler(CommandHandler('restart', restart_command))
    app.add_handler(CommandHandler('temp', temp_command))
    app.add_handler(CommandHandler('snapshot', snapshot_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('more', more_command))
    app.add_handler(CommandHandler('home', home_command))
    app.add_handler(CommandHandler('info', info_command))
    app.add_handler(CommandHandler('macros', macros_command))
    app.add_handler(CommandHandler('job', job_command))
    app.add_handler(CommandHandler('exec', exec_command))
    app.add_handler(CallbackQueryHandler(exec_macro_callback, pattern="^exec_macro:"))
    print("🤖 Bot is running!")
    app.run_polling()

if __name__ == '__main__':
    main()
