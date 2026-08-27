
---

### `main.py`

```python
import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

# Load environment variables
load_dotenv()

# ===== LOGGING =====
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ===== CONFIGURATION =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

# ===== CONVERSATION STATES =====
GAME_NAME, ACHIEVEMENT, DATE = range(3)

# ===== DATABASE (In-memory for demo - use PostgreSQL in production) =====
users_data: Dict[int, Dict] = {}
milestones: Dict[int, List[Dict]] = {}

@dataclass
class Milestone:
    game_name: str
    achievement: str
    date: str
    milestone_id: int

def get_user_data(user_id: int) -> Dict:
    """Get or create user data."""
    if user_id not in users_data:
        users_data[user_id] = {
            "points": 0,
            "streak": 0,
            "first_name": "",
            "milestones": [],
            "last_activity": None,
        }
    return users_data[user_id]

# ===== SAMPLE MILESTONE SUGGESTIONS =====
SAMPLE_MILESTONES = {
    "First Win": "🎮 Your first victory in a competitive game",
    "Level Up": "⭐ Reached a new level milestone",
    "Rank Up": "🏆 Achieved a new competitive rank",
    "Achievement": "🎯 Unlocked a rare achievement",
    "1000 Hours": "⏰ Played 1000+ hours in a game",
    "First Game": "🎮 Started playing a new game",
    "Return": "🔄 Returned to a game after a break",
}

# ===== KEYBOARDS =====

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create the main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🎮 Track Milestone", callback_data="track")],
        [InlineKeyboardButton("📋 My History", callback_data="history")],
        [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("💡 Suggestions", callback_data="suggestions")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_menu_keyboard() -> InlineKeyboardMarkup:
    """Create a keyboard with back to menu button."""
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")]]
    return InlineKeyboardMarkup(keyboard)

def get_stats_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for stats page."""
    keyboard = [
        [InlineKeyboardButton("🎮 Track New", callback_data="track")],
        [InlineKeyboardButton("📋 My History", callback_data="history")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_suggestions_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for milestone suggestions."""
    keyboard = [
        [InlineKeyboardButton("🎮 First Win", callback_data="suggest_first_win")],
        [InlineKeyboardButton("⭐ Level Up", callback_data="suggest_level_up")],
        [InlineKeyboardButton("🏆 Rank Up", callback_data="suggest_rank_up")],
        [InlineKeyboardButton("🎯 Achievement", callback_data="suggest_achievement")],
        [InlineKeyboardButton("⏰ 1000 Hours", callback_data="suggest_1000_hours")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== COMMAND HANDLERS =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when /start is issued."""
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name or "Player"
    
    # Initialize user data
    user_data = get_user_data(user_id)
    user_data["first_name"] = first_name
    
    welcome_text = f"""🎉 *Welcome to Anni-Versary, {first_name}!*

I help you track your gaming milestones, anniversaries, and achievements — completely free.

*Here's what I can do for you:*
🎮 *Track Milestones* - Log your gaming achievements
📋 *View History* - See all your milestones
📊 *Stats Dashboard* - Track your progress
🏆 *Leaderboard* - Compete with friends
💡 *Suggestions* - Get milestone ideas

*No gambling. Just gaming memories.* 🎯

Tap a button below to get started!"""

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when /help is issued."""
    help_text = """📖 *Anni-Versary - Help*

*Commands:*
/start - Main menu
/help - This message
/track - Track a new milestone
/history - View your milestone history
/stats - Your stats
/leaderboard - Top players

*How it works:*
1️⃣ Track your gaming milestones
2️⃣ Build your gaming history
3️⃣ Compete with others
4️⃣ Celebrate your achievements

*Everything is free - no gambling!* 🎮"""

    await update.message.reply_text(
        help_text,
        reply_markup=get_back_menu_keyboard(),
        parse_mode="Markdown",
    )


async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start tracking a new milestone."""
    track_text = """🎮 *Track a New Milestone*

Enter the name of the game you want to track.

*Example:* "Counter-Strike 2" or "Valorant"

You can also use the suggestions below! 💡"""

    keyboard = [
        [InlineKeyboardButton("💡 View Suggestions", callback_data="suggestions")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        track_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return GAME_NAME


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's milestone history."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    milestones_list = user_data.get("milestones", [])
    
    if not milestones_list:
        history_text = """📋 *Your Milestone History*

You haven't tracked any milestones yet! 🎮

Tap the button below to track your first milestone!"""
        
        keyboard = [[InlineKeyboardButton("🎮 Track First", callback_data="track")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            history_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        return
    
    history_text = "📋 *Your Milestone History*\n\n"
    for i, milestone in enumerate(milestones_list[-10:], 1):  # Show last 10
        history_text += f"{i}. 🎮 *{milestone['game_name']}*\n"
        history_text += f"   🏆 {milestone['achievement']}\n"
        history_text += f"   📅 {milestone['date']}\n\n"
    
    if len(milestones_list) > 10:
        history_text += f"*Showing last 10 of {len(milestones_list)} milestones.*"
    
    keyboard = [
        [InlineKeyboardButton("🎮 Track New", callback_data="track")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        history_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user stats."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    first_name = user_data.get("first_name", update.effective_user.first_name or "Player")
    milestones_list = user_data.get("milestones", [])
    
    # Calculate rank
    sorted_users = sorted(
        users_data.items(), 
        key=lambda x: len(x[1].get("milestones", [])), 
        reverse=True
    )
    rank = next(
        (i + 1 for i, (uid, _) in enumerate(sorted_users) if uid == user_id),
        len(users_data),
    )
    
    stats_text = f"""📊 *My Stats*

👤 Player: {first_name}
🏆 Milestones: {len(milestones_list)}
⭐ Points: {user_data['points']}
🔥 Streak: {user_data['streak']} days
📊 Rank: #{rank} on leaderboard

Keep tracking your gaming journey! 🎮"""

    await update.message.reply_text(
        stats_text,
        reply_markup=get_stats_keyboard(),
        parse_mode="Markdown",
    )


async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show leaderboard."""
    if not users_data:
        leaderboard_text = "🏆 *Leaderboard*\n\nNo players yet! Be the first to track a milestone! 🎮"
    else:
        sorted_users = sorted(
            users_data.items(), 
            key=lambda x: len(x[1].get("milestones", [])), 
            reverse=True
        )
        
        leaderboard_text = "🏆 *Leaderboard*\n\n"
        for i, (user_id, data) in enumerate(sorted_users[:10], 1):
            first_name = data.get("first_name", f"Player_{str(user_id)[:6]}")
            milestone_count = len(data.get("milestones", []))
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leaderboard_text += f"{medal} {first_name} - {milestone_count} milestones\n"
    
    keyboard = [
        [InlineKeyboardButton("🎮 Track New", callback_data="track")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        leaderboard_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def suggestions_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show milestone suggestions."""
    suggestions_text = """💡 *Milestone Suggestions*

Here are some ideas for milestones to track:

🎮 *First Win* - Your first victory in a competitive game
⭐ *Level Up* - Reached a new level milestone
🏆 *Rank Up* - Achieved a new competitive rank
🎯 *Achievement* - Unlocked a rare achievement
⏰ *1000 Hours* - Played 1000+ hours in a game
🎮 *First Game* - Started playing a new game
🔄 *Return* - Returned to a game after a break

*Tap a suggestion below to use it!* 👇"""

    await update.message.reply_text(
        suggestions_text,
        reply_markup=get_suggestions_keyboard(),
        parse_mode="Markdown",
    )


# ===== CONVERSATION HANDLERS =====

async def track_milestone_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start milestone tracking conversation."""
    track_text = """🎮 *Track a New Milestone*

Enter the name of the game you want to track.

*Example:* "Counter-Strike 2" or "Valorant"

You can also use the suggestions below! 💡"""

    keyboard = [
        [InlineKeyboardButton("💡 View Suggestions", callback_data="suggestions")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        track_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return GAME_NAME


async def track_game_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle game name input."""
    context.user_data["game_name"] = update.message.text
    
    achievement_text = """🏆 *What was your achievement?*

Describe the milestone you reached.

*Examples:*
- "First win in competitive mode"
- "Reached Diamond rank"
- "1000 hours played"
- "Unlocked all achievements"

Be as specific as you like! 🎯"""

    await update.message.reply_text(
        achievement_text,
        reply_markup=get_back_menu_keyboard(),
        parse_mode="Markdown",
    )
    return ACHIEVEMENT


async def track_achievement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle achievement input."""
    context.user_data["achievement"] = update.message.text
    
    date_text = """📅 *When did this happen?*

Enter the date in one of these formats:
- Today (for today's date)
- Yesterday (for yesterday's date)
- MM/DD/YYYY (e.g., 12/25/2024)
- 2024-12-25 (YYYY-MM-DD)

Or just type a date like "December 25, 2024" 🗓️"""

    await update.message.reply_text(
        date_text,
        reply_markup=get_back_menu_keyboard(),
        parse_mode="Markdown",
    )
    return DATE


async def track_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle date input and save milestone."""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    date_input = update.message.text.strip().lower()
    
    # Parse date
    today = datetime.now().date()
    if date_input == "today":
        date_str = today.strftime("%B %d, %Y")
    elif date_input == "yesterday":
        date_str = (today - timedelta(days=1)).strftime("%B %d, %Y")
    else:
        # Try to parse various date formats
        try:
            # Try MM/DD/YYYY
            parsed_date = datetime.strptime(date_input, "%m/%d/%Y").date()
            date_str = parsed_date.strftime("%B %d, %Y")
        except ValueError:
            try:
                # Try YYYY-MM-DD
                parsed_date = datetime.strptime(date_input, "%Y-%m-%d").date()
                date_str = parsed_date.strftime("%B %d, %Y")
            except ValueError:
                # If all fails, use what user provided
                date_str = date_input
    
    # Save milestone
    game_name = context.user_data.get("game_name", "Unknown Game")
    achievement = context.user_data.get("achievement", "Achievement unlocked!")
    
    milestone = {
        "game_name": game_name,
        "achievement": achievement,
        "date": date_str,
        "tracked_at": datetime.now().isoformat(),
    }
    
    if "milestones" not in user_data:
        user_data["milestones"] = []
    user_data["milestones"].append(milestone)
    
    # Update points and streak
    user_data["points"] += 10
    today_date = today
    if user_data.get("last_activity") == today_date:
        user_data["streak"] += 1
    else:
        user_data["streak"] = 1
    user_data["last_activity"] = today_date
    
    # Success message
    success_text = f"""🎉 *Milestone Tracked!*

🎮 *Game:* {game_name}
🏆 *Achievement:* {achievement}
📅 *Date:* {date_str}

✨ *+10 points earned!*
📊 Points: {user_data['points']} | Streak: {user_data['streak']} days
🏆 Total Milestones: {len(user_data['milestones'])}

Keep tracking your gaming journey! 🎮"""

    keyboard = [
        [InlineKeyboardButton("🎮 Track Another", callback_data="track")],
        [InlineKeyboardButton("📋 My History", callback_data="history")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        success_text,
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    
    # Clean up context
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel milestone tracking."""
    await update.message.reply_text(
        "❌ Milestone tracking cancelled.",
        reply_markup=get_back_menu_keyboard(),
    )
    context.user_data.clear()
    return ConversationHandler.END


# ===== CALLBACK QUERY HANDLERS =====

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    first_name = user_data.get("first_name", update.effective_user.first_name or "Player")
    
    if data == "menu":
        welcome_text = f"""🎉 *Welcome back, {first_name}!*

What would you like to do?"""
        
        await query.edit_message_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown",
        )
    
    elif data == "track":
        # Start tracking conversation inline
        track_text = """🎮 *Track a New Milestone*

Enter the name of the game you want to track.

*Example:* "Counter-Strike 2" or "Valorant"

You can also use the suggestions below! 💡"""

        keyboard = [
            [InlineKeyboardButton("💡 View Suggestions", callback_data="suggestions")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            track_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        # Set state for text input
        context.user_data["awaiting_track"] = True
    
    elif data == "history":
        milestones_list = user_data.get("milestones", [])
        
        if not milestones_list:
            history_text = """📋 *Your Milestone History*

You haven't tracked any milestones yet! 🎮

Tap the button below to track your first milestone!"""
            
            keyboard = [[InlineKeyboardButton("🎮 Track First", callback_data="track")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                history_text,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
            return
        
        history_text = "📋 *Your Milestone History*\n\n"
        for i, milestone in enumerate(milestones_list[-10:], 1):
            history_text += f"{i}. 🎮 *{milestone['game_name']}*\n"
            history_text += f"   🏆 {milestone['achievement']}\n"
            history_text += f"   📅 {milestone['date']}\n\n"
        
        if len(milestones_list) > 10:
            history_text += f"*Showing last 10 of {len(milestones_list)} milestones.*"
        
        keyboard = [
            [InlineKeyboardButton("🎮 Track New", callback_data="track")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            history_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    
    elif data == "stats":
        milestones_list = user_data.get("milestones", [])
        
        sorted_users = sorted(
            users_data.items(), 
            key=lambda x: len(x[1].get("milestones", [])), 
            reverse=True
        )
        rank = next(
            (i + 1 for i, (uid, _) in enumerate(sorted_users) if uid == user_id),
            len(users_data),
        )
        
        stats_text = f"""📊 *My Stats*

👤 Player: {first_name}
🏆 Milestones: {len(milestones_list)}
⭐ Points: {user_data['points']}
🔥 Streak: {user_data['streak']} days
📊 Rank: #{rank} on leaderboard

Keep tracking your gaming journey! 🎮"""
        
        await query.edit_message_text(
            stats_text,
            reply_markup=get_stats_keyboard(),
            parse_mode="Markdown",
        )
    
    elif data == "leaderboard":
        if not users_data:
            leaderboard_text = "🏆 *Leaderboard*\n\nNo players yet! Be the first to track a milestone! 🎮"
        else:
            sorted_users = sorted(
                users_data.items(), 
                key=lambda x: len(x[1].get("milestones", [])), 
                reverse=True
            )
            
            leaderboard_text = "🏆 *Leaderboard*\n\n"
            for i, (uid, data_dict) in enumerate(sorted_users[:10], 1):
                name = data_dict.get("first_name", f"Player_{str(uid)[:6]}")
                milestone_count = len(data_dict.get("milestones", []))
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                leaderboard_text += f"{medal} {name} - {milestone_count} milestones\n"
        
        keyboard = [
            [InlineKeyboardButton("🎮 Track New", callback_data="track")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            leaderboard_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
    
    elif data == "suggestions":
        suggestions_text = """💡 *Milestone Suggestions*

Here are some ideas for milestones to track:

🎮 *First Win* - Your first victory in a competitive game
⭐ *Level Up* - Reached a new level milestone
🏆 *Rank Up* - Achieved a new competitive rank
🎯 *Achievement* - Unlocked a rare achievement
⏰ *1000 Hours* - Played 1000+ hours in a game
🎮 *First Game* - Started playing a new game
🔄 *Return* - Returned to a game after a break

*Tap a suggestion below to track it quickly!* 👇"""

        await query.edit_message_text(
            suggestions_text,
            reply_markup=get_suggestions_keyboard(),
            parse_mode="Markdown",
        )
    
    # Suggestion quick-add handlers
    elif data.startswith("suggest_"):
        suggestion_type = data.replace("suggest_", "")
        suggestions = {
            "first_win": {"game": "Competitive Gaming", "achievement": "First win in competitive mode"},
            "level_up": {"game": "Gaming Journey", "achievement": "Reached a new level milestone"},
            "rank_up": {"game": "Competitive Gaming", "achievement": "Achieved a new competitive rank"},
            "achievement": {"game": "Gaming Journey", "achievement": "Unlocked a rare achievement"},
            "1000_hours": {"game": "Gaming Journey", "achievement": "Played 1000+ hours"},
        }
        
        suggestion = suggestions.get(suggestion_type, {"game": "Gaming", "achievement": "Milestone reached"})
        
        # Save the milestone immediately
        today = datetime.now().date()
        milestone = {
            "game_name": suggestion["game"],
            "achievement": suggestion["achievement"],
            "date": today.strftime("%B %d, %Y"),
            "tracked_at": datetime.now().isoformat(),
        }
        
        if "milestones" not in user_data:
            user_data["milestones"] = []
        user_data["milestones"].append(milestone)
        
        user_data["points"] += 10
        if user_data.get("last_activity") == today:
            user_data["streak"] += 1
        else:
            user_data["streak"] = 1
        user_data["last_activity"] = today
        
        success_text = f"""🎉 *Milestone Tracked!*

🎮 *Game:* {suggestion['game']}
🏆 *Achievement:* {suggestion['achievement']}
📅 *Date:* {today.strftime("%B %d, %Y")}

✨ *+10 points earned!*
📊 Points: {user_data['points']} | Streak: {user_data['streak']} days
🏆 Total Milestones: {len(user_data['milestones'])}

Keep tracking your gaming journey! 🎮"""

        keyboard = [
            [InlineKeyboardButton("🎮 Track Another", callback_data="track")],
            [InlineKeyboardButton("📋 My History", callback_data="history")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            success_text,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )


# ===== MESSAGE HANDLER (for inline tracking) =====

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text input for tracking."""
    if context.user_data.get("awaiting_track"):
        # This is a simplified tracking - user enters: Game Name | Achievement | Date
        text = update.message.text
        parts = text.split("|")
        
        if len(parts) >= 2:
            game_name = parts[0].strip()
            achievement = parts[1].strip()
            date_part = parts[2].strip() if len(parts) > 2 else "today"
            
            # Parse date
            today = datetime.now().date()
            if date_part.lower() == "today":
                date_str = today.strftime("%B %d, %Y")
            elif date_part.lower() == "yesterday":
                date_str = (today - timedelta(days=1)).strftime("%B %d, %Y")
            else:
                try:
                    parsed_date = datetime.strptime(date_part, "%m/%d/%Y").date()
                    date_str = parsed_date.strftime("%B %d, %Y")
                except ValueError:
                    try:
                        parsed_date = datetime.strptime(date_part, "%Y-%m-%d").date()
                        date_str = parsed_date.strftime("%B %d, %Y")
                    except ValueError:
                        date_str = date_part
            
            user_id = update.effective_user.id
            user_data = get_user_data(user_id)
            
            milestone = {
                "game_name": game_name,
                "achievement": achievement,
                "date": date_str,
                "tracked_at": datetime.now().isoformat(),
            }
            
            if "milestones" not in user_data:
                user_data["milestones"] = []
            user_data["milestones"].append(milestone)
            
            user_data["points"] += 10
            if user_data.get("last_activity") == today:
                user_data["streak"] += 1
            else:
                user_data["streak"] = 1
            user_data["last_activity"] = today
            
            success_text = f"""🎉 *Milestone Tracked!*

🎮 *Game:* {game_name}
🏆 *Achievement:* {achievement}
📅 *Date:* {date_str}

✨ *+10 points earned!*
📊 Points: {user_data['points']} | Streak: {user_data['streak']} days
🏆 Total Milestones: {len(user_data['milestones'])}

Keep tracking your gaming journey! 🎮"""
            
            keyboard = [
                [InlineKeyboardButton("🎮 Track Another", callback_data="track")],
                [InlineKeyboardButton("📋 My History", callback_data="history")],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                success_text,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
            context.user_data["awaiting_track"] = False
        else:
            await update.message.reply_text(
                "❌ *Invalid format!*\n\nPlease use this format:\n`Game Name | Achievement | Date`\n\n*Example:* `Counter-Strike 2 | First win | today`",
                parse_mode="Markdown",
                reply_markup=get_back_menu_keyboard(),
            )


# ===== ERROR HANDLER =====

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)


# ===== MAIN FUNCTION =====

def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register conversation handler for tracking
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("track", track_milestone_start),
            CallbackQueryHandler(lambda u, c: track_milestone_start(u, c), pattern="^track$"),
        ],
        states={
            GAME_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, track_game_name)],
            ACHIEVEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, track_achievement)],
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, track_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel_tracking)],
    )
    
    application.add_handler(conv_handler)
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("leaderboard", leaderboard_command))
    application.add_handler(CommandHandler("suggestions", suggestions_command))
    
    # Register callback query handler for buttons
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Register message handler for inline tracking
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    # Register error handler
    application.add_error_handler(error_handler)

    # Run the bot
    print("🚀 Anni-Versary Bot is running...")
    print("🤖 Bot username: @Anni_versary_bot")
    print("📋 Available commands: /start, /help, /track, /history, /stats, /leaderboard, /suggestions")
    print("⚠️  Press Ctrl+C to stop")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
