# Anni-Versary Bot 🎉

A Telegram bot that helps gamers track their gaming milestones, anniversaries, and achievements.

## Features

- 🎮 **Track Milestones** - Log your gaming achievements
- 📅 **Anniversary Reminders** - Remember important gaming dates
- 📊 **Stats Dashboard** - View your progress
- 🏆 **Leaderboard** - Compete with friends
- 📂 **Categories** - Organize by game or achievement type

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Main menu with welcome message |
| `/help` | Help and available commands |
| `/track` | Track a new milestone |
| `/history` | View your milestone history |
| `/stats` | View your stats |
| `/leaderboard` | View top players |

## Bot Information

- **Username:** @Anni_versary_bot
- **Purpose:** Track gaming milestones and achievements
- **Content:** Free - no gambling

## Installation

```bash
git clone https://github.com/yourusername/anni-versary-bot.git
cd anni-versary-bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your bot token
python main.py
