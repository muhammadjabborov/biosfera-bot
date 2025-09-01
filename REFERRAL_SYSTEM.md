# Referral System Documentation

## Overview
The referral system allows confirmed teachers to earn points by referring other users to the bot. When users reach a certain point threshold, they receive invite links to channels.

## How It Works

### 1. Referral Process
- When a user starts the bot with a referral parameter (e.g., `/start 123456789`), the system checks if the referrer exists
- If the referrer is a confirmed teacher, they receive 1 point for each successful referral
- Users cannot refer themselves
- Each user can only be referred once

### 2. Points System
- Points are only awarded to confirmed teachers (`is_confirmed=True`)
- Points are stored in the `Point` model
- The point threshold for receiving invite links is configurable via the `PointScore` model

### 3. Invite Links
- When a user reaches the point threshold, they automatically receive invite links to configured channels
- Links are sent only once per user (tracked by `LinkGot` model)
- Channel information is stored in the `ChannelID` model

## Models

### Point
- `user`: ForeignKey to User
- `points`: IntegerField (default: 0)

### PointScore
- `points`: IntegerField (default: 0) - threshold for invite links

### LinkGot
- `user`: ForeignKey to User
- `is_get`: BooleanField (default: False) - tracks if user received links

### Referral
- `referrer`: ForeignKey to User (who referred)
- `referee`: ForeignKey to User (who was referred)

### ChannelID
- `channel_name`: CharField - display name for the channel
- `channel_id`: CharField - Telegram channel ID

## Setup Instructions

### 1. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Set Up Default Data
```bash
python manage.py setup_referral_system
```

### 3. Configure Channels (via Admin)
1. Go to Django Admin
2. Add channels in the "Channel IDs" section
3. Enter channel name and channel ID

### 4. Configure Point Threshold (via Admin)
1. Go to Django Admin
2. Edit the "Point Score" entry
3. Set the desired point threshold

## Usage

### For Users
1. **View Referral Info**: Click "🔗 Referal" to see referral count and link
2. **View Points**: Click "🏆 Mening ballarim" to see current points and status
3. **Share Referral Link**: Share the generated referral link with friends

### For Admins
1. **Monitor Referrals**: View all referrals in the admin panel
2. **Manage Points**: Edit user points if needed
3. **Configure Channels**: Add/remove channels for invite links
4. **Set Threshold**: Adjust the point threshold for invite links

## Bot Commands

- `/start` - Start the bot
- `/start <user_id>` - Start with referral (where user_id is the referrer's Telegram ID)

## Features

- ✅ Automatic point calculation for confirmed teachers
- ✅ Prevention of self-referrals
- ✅ One-time referral per user
- ✅ Automatic invite link distribution
- ✅ Admin panel for management
- ✅ Point threshold configuration
- ✅ Channel management

## Notes

- Only confirmed teachers (`is_confirmed=True`) can earn points
- Invite links are sent automatically when threshold is reached
- Links are sent only once per user
- The system logs all referral activities for debugging
