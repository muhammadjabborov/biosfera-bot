# Biosfera Bot Setup Guide

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
HOST=localhost

# Database Settings
DB_ENGINE=django.db.backends.postgresql
DB_NAME=biosfera_bot
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Redis Settings
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379

# Telegram Bot Settings
BOT_TOKEN=your-telegram-bot-token-here
CHANNEL_ID=@your_admin_channel_username
```

## Required Setup

1. **Telegram Bot Token**: Get from @BotFather
2. **Admin Channel**: Create a channel and add your bot as admin
3. **CHANNEL_ID**: Use the channel username (e.g., @admin_channel) or channel ID

## Features

### Teacher Registration Flow
- Full name input
- Phone number (with contact sharing option)
- Region selection (inline buttons)
- District selection (inline buttons)
- School name input
- Toifa selection (Oliy, 1-toifa, 2-toifa, Mutaxassis, Yo'q)
- Document upload (if toifa is not "Yo'q")

### Admin Review
- All applications with documents are sent to the admin channel
- Admin can accept or reject with inline buttons
- Users are notified of the decision

### Profile Management
- Users can view their profile with `/profile` command
- Existing users can update their information
- Confirmed teachers get full access

## Database Models

- **User**: Basic user information
- **Teacher**: Teacher profile with all registration details
- **Region/District**: Geographic data for selection

## State Management

The bot uses **aiogram's built-in state management** instead of database models for registration flow:
- **Memory-based**: Fast, no database queries during registration
- **Automatic cleanup**: States are cleared after completion or cancellation
- **Efficient**: Data is stored in memory during the registration process
- **Standard practice**: This is how aiogram is designed to work

## Running the Bot

1. Install dependencies: `pip install -r requirements/develop.txt`
2. Run migrations: `python manage.py migrate`
3. Start the bot: `python manage.py runbot`

## Notes

- Documents are sent directly to admin channel without storing in database
- Users with "Yo'q" toifa are auto-confirmed
- All text is in Uzbek language
- Registration states are managed by aiogram (in-memory)
- No custom database models needed for registration flow 