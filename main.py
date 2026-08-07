import os
import logging
import datetime
import json
from telebot import TeleBot, types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    logging.error("TELEGRAM_BOT_TOKEN environment variable not set!")
    exit(1)

bot = TeleBot(BOT_TOKEN)

# Simple in-memory storage (for production, use a database)
user_data = {}  # user_id: {"anniversaries": [], "name": ""}

# --- Helper Functions ---

def get_date_from_string(date_str):
    """Convert string to date object"""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

def get_days_until(date_obj):
    """Calculate days until a date"""
    today = datetime.datetime.now().date()
    if date_obj < today:
        # If date has passed this year, calculate for next year
        date_obj = date_obj.replace(year=today.year + 1)
    delta = date_obj - today
    return delta.days

def format_anniversary(anniversary):
    """Format anniversary for display"""
    name = anniversary.get("name", "Unnamed")
    date_obj = anniversary.get("date")
    days_until = get_days_until(date_obj)
    
    if days_until == 0:
        status = "🎉 **TODAY!**"
    elif days_until == 1:
        status = "⏰ **Tomorrow!**"
    elif days_until <= 7:
        status = f"⏳ **{days_until} days**"
    else:
        status = f"📅 **{days_until} days**"
    
    return f"• **{name}** - {date_obj.strftime('%B %d, %Y')} ({status})"

def get_upcoming_anniversaries(user_id, days_ahead=30):
    """Get upcoming anniversaries within days_ahead"""
    if user_id not in user_data:
        return []
    
    anniversaries = user_data[user_id].get("anniversaries", [])
    upcoming = []
    
    for anniv in anniversaries:
        date_obj = anniv.get("date")
        days_until = get_days_until(date_obj)
        if 0 <= days_until <= days_ahead:
            upcoming.append(anniv)
    
    return sorted(upcoming, key=lambda x: get_days_until(x["date"]))

# --- Command Handlers ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Welcome message"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    if user_id not in user_data:
        user_data[user_id] = {
            "anniversaries": [],
            "name": user_name
        }
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("➕ Add Date", callback_data="add_date"),
        InlineKeyboardButton("📋 My Dates", callback_data="my_dates")
    )
    markup.add(
        InlineKeyboardButton("⏰ Upcoming", callback_data="upcoming"),
        InlineKeyboardButton("ℹ️ About", callback_data="about")
    )
    
    welcome_text = (
        f"🎉 Welcome, {user_name}!\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 **Anniversary Tracker**\n\n"
        f"Never forget special dates again!\n"
        f"• 📌 Save anniversaries & birthdays\n"
        f"• ⏰ Get reminders\n"
        f"• 🎯 Track upcoming dates\n\n"
        f"**Start tracking now:**"
    )
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(commands=['add'])
def add_anniversary_command(message):
    """Start add anniversary process"""
    msg = bot.send_message(
        message.chat.id,
        "📝 **Add a Special Date**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Please enter the **name** of the date:\n"
        "(e.g., \"My Birthday\", \"Anniversary\", \"Mom's Birthday\")\n\n"
        "Type **/cancel** to cancel.",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, get_anniversary_name)

def get_anniversary_name(message):
    """Get anniversary name from user"""
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "❌ Cancelled.", parse_mode='Markdown')
        return
    
    user_id = message.from_user.id
    if user_id not in user_data:
        user_data[user_id] = {"anniversaries": [], "name": message.from_user.first_name}
    
    # Store temporary data
    if "temp" not in user_data[user_id]:
        user_data[user_id]["temp"] = {}
    user_data[user_id]["temp"]["name"] = message.text
    
    msg = bot.send_message(
        message.chat.id,
        f"📝 **Date Name:** {message.text}\n\n"
        "Now enter the **date** (YYYY-MM-DD):\n"
        "(e.g., 1990-05-15)\n\n"
        "Type **/cancel** to cancel.",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, get_anniversary_date)

def get_anniversary_date(message):
    """Get anniversary date from user"""
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "❌ Cancelled.", parse_mode='Markdown')
        return
    
    user_id = message.from_user.id
    date_obj = get_date_from_string(message.text)
    
    if not date_obj:
        msg = bot.send_message(
            message.chat.id,
            "❌ Invalid date format. Please use YYYY-MM-DD.\n\n"
            "Try again or type **/cancel**.",
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, get_anniversary_date)
        return
    
    # Save the anniversary
    name = user_data[user_id]["temp"]["name"]
    anniversary = {
        "name": name,
        "date": date_obj,
        "added": datetime.datetime.now().isoformat()
    }
    
    user_data[user_id]["anniversaries"].append(anniversary)
    
    # Clean up temp data
    del user_data[user_id]["temp"]
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("➕ Add Another", callback_data="add_date"),
        InlineKeyboardButton("📋 My Dates", callback_data="my_dates")
    )
    
    days_until = get_days_until(date_obj)
    days_text = "today!" if days_until == 0 else f"in {days_until} days"
    
    bot.send_message(
        message.chat.id,
        f"✅ **Saved!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 **{name}** - {date_obj.strftime('%B %d, %Y')}\n"
        f"⏰ Next occurrence: {days_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.message_handler(commands=['list'])
def list_anniversaries_command(message):
    """List all anniversaries via command"""
    handle_my_dates(message.chat.id, message.from_user.id)

@bot.message_handler(commands=['upcoming'])
def upcoming_command(message):
    """Show upcoming anniversaries via command"""
    handle_upcoming(message.chat.id, message.from_user.id)

@bot.message_handler(commands=['delete'])
def delete_command(message):
    """Delete an anniversary"""
    user_id = message.from_user.id
    if user_id not in user_data or not user_data[user_id]["anniversaries"]:
        bot.send_message(
            message.chat.id,
            "📭 You don't have any dates saved yet.",
            parse_mode='Markdown'
        )
        return
    
    # Show list with numbers to delete
    anniversaries = user_data[user_id]["anniversaries"]
    text = "🗑️ **Delete a Date**\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, anniv in enumerate(anniversaries, 1):
        text += f"{i}. {anniv['name']} - {anniv['date'].strftime('%B %d, %Y')}\n"
    text += "\nType the **number** of the date to delete or **/cancel**."
    
    msg = bot.send_message(message.chat.id, text, parse_mode='Markdown')
    bot.register_next_step_handler(msg, delete_anniversary_by_number)

def delete_anniversary_by_number(message):
    """Delete anniversary by number"""
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "❌ Cancelled.", parse_mode='Markdown')
        return
    
    user_id = message.from_user.id
    try:
        index = int(message.text) - 1
        anniversaries = user_data[user_id]["anniversaries"]
        if 0 <= index < len(anniversaries):
            removed = anniversaries.pop(index)
            bot.send_message(
                message.chat.id,
                f"✅ Deleted: **{removed['name']}**",
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                message.chat.id,
                "❌ Invalid number. Please try again.",
                parse_mode='Markdown'
            )
    except ValueError:
        bot.send_message(
            message.chat.id,
            "❌ Please enter a valid number.",
            parse_mode='Markdown'
        )

@bot.message_handler(commands=['help'])
def send_help(message):
    """Help command"""
    help_text = (
        "📖 **Commands**\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "• `/start` - Main menu\n"
        "• `/add` - Add a special date\n"
        "• `/list` - View all dates\n"
        "• `/upcoming` - See upcoming dates\n"
        "• `/delete` - Delete a date\n"
        "• `/help` - This message\n\n"
        "📌 **How it works:**\n"
        "Save any special date\n"
        "Get reminded before it arrives\n"
        "Never miss important days again!\n\n"
        "🎯 **Free & useful!**"
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    """Handle any other messages"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📂 Menu", callback_data="start"))
    
    response = (
        "💡 **Use commands or buttons:**\n\n"
        "• `/add` - Add a date\n"
        "• `/list` - View all dates\n"
        "• `/upcoming` - Upcoming dates\n"
        "• `/delete` - Delete a date"
    )
    bot.reply_to(message, response, parse_mode='Markdown', reply_markup=markup)

# --- Handler Functions ---

def handle_my_dates(chat_id, user_id):
    """Show all saved anniversaries"""
    if user_id not in user_data or not user_data[user_id]["anniversaries"]:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("➕ Add Date", callback_data="add_date"))
        
        bot.send_message(
            chat_id,
            "📭 **No dates saved yet.**\n\n"
            "Add your first special date now!",
            parse_mode='Markdown',
            reply_markup=markup
        )
        return
    
    anniversaries = user_data[user_id]["anniversaries"]
    text = "📋 **My Special Dates**\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for anniv in anniversaries:
        text += format_anniversary(anniv) + "\n"
    
    text += "\n━━━━━━━━━━━━━━━━━━━━"
    text += f"\n📊 **Total:** {len(anniversaries)} dates"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("➕ Add Date", callback_data="add_date"),
        InlineKeyboardButton("⏰ Upcoming", callback_data="upcoming")
    )
    markup.add(InlineKeyboardButton("🔙 Menu", callback_data="start"))
    
    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)

def handle_upcoming(chat_id, user_id):
    """Show upcoming anniversaries"""
    if user_id not in user_data or not user_data[user_id]["anniversaries"]:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("➕ Add Date", callback_data="add_date"))
        
        bot.send_message(
            chat_id,
            "📭 **No dates saved yet.**\n\n"
            "Add your first special date now!",
            parse_mode='Markdown',
            reply_markup=markup
        )
        return
    
    upcoming = get_upcoming_anniversaries(user_id, 30)
    
    if not upcoming:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("📋 My Dates", callback_data="my_dates"),
            InlineKeyboardButton("➕ Add Date", callback_data="add_date")
        )
        
        bot.send_message(
            chat_id,
            "🎯 **No upcoming dates in the next 30 days.**\n\n"
            "Check all your saved dates or add more!",
            parse_mode='Markdown',
            reply_markup=markup
        )
        return
    
    text = "⏰ **Upcoming Dates (Next 30 Days)**\n━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for anniv in upcoming:
        text += format_anniversary(anniv) + "\n"
    
    text += "\n━━━━━━━━━━━━━━━━━━━━"
    text += f"\n📊 **Total:** {len(upcoming)} upcoming dates"
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("📋 My Dates", callback_data="my_dates"),
        InlineKeyboardButton("➕ Add Date", callback_data="add_date")
    )
    markup.add(InlineKeyboardButton("🔙 Menu", callback_data="start"))
    
    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)

# --- Callback Handlers ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    """Handle button clicks"""
    try:
        if call.data == "start":
            send_welcome(call.message)
            bot.answer_callback_query(call.id)
            
        elif call.data == "add_date":
            # Trigger the add command
            add_anniversary_command(call.message)
            bot.answer_callback_query(call.id)
            
        elif call.data == "my_dates":
            handle_my_dates(call.message.chat.id, call.from_user.id)
            bot.answer_callback_query(call.id)
            
        elif call.data == "upcoming":
            handle_upcoming(call.message.chat.id, call.from_user.id)
            bot.answer_callback_query(call.id)
            
        elif call.data == "about":
            about_text = (
                "🤖 **About Anniversary Bot**\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "Never forget special dates!\n\n"
                "✅ Save anniversaries & birthdays\n"
                "✅ Get reminders\n"
                "✅ Track upcoming dates\n"
                "✅ Free & easy to use\n\n"
                "📌 **Perfect for:**\n"
                "• 🎂 Birthdays\n"
                "• 💍 Anniversaries\n"
                "• 🎓 Graduations\n"
                "• 🎉 Any special day\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"👥 {len(user_data)} users"
            )
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 Menu", callback_data="start"))
            
            bot.edit_message_text(
                about_text,
                call.message.chat.id,
                call.message.message_id,
                parse_mode='Markdown',
                reply_markup=markup
            )
            bot.answer_callback_query(call.id)
            
    except Exception as e:
        logging.error(f"Callback error: {e}")
        bot.answer_callback_query(call.id, text="❌ Error", show_alert=True)

# --- Main Execution ---

if __name__ == '__main__':
    logging.info("🚀 Anniversary Bot is starting...")
    logging.info(f"✅ Bot online! Users: {len(user_data)}")
    
    # Check for upcoming anniversaries daily (in production, use a scheduler)
    # For now, we'll just run the bot
    
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logging.error(f"Bot polling failed: {e}")
