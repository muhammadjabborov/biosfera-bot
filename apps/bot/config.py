from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
from django.conf import settings

storage = MemoryStorage()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(bot, storage=storage)

# Channel ID for admin notifications
CHANNEL_ID = getattr(settings, 'CHANNEL_ID', None)
