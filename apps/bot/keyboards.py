from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from apps.common.models import Region, District
from apps.bot.models import TOIFA_CHOICES


def get_main_keyboard():
    """Asosiy klaviatura"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(KeyboardButton("📝 Ro'yxatdan o'tish"))
    return keyboard


def get_registered_user_keyboard():
    """Tasdiqlangan foydalanuvchilar uchun klaviatura"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(KeyboardButton("🔗 Referal"), (KeyboardButton("🏆 Mening ballarim")))
    keyboard.add(KeyboardButton("👤 Profil"))
    return keyboard


def get_statistics_keyboard():
    """Statistika darajalari klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🏘️ Tuman boyicha", callback_data="stats_district"),
        InlineKeyboardButton("🏛️ Viloyat boyicha", callback_data="stats_region"),
        InlineKeyboardButton("🇺🇿 Respublika boyicha", callback_data="stats_republic"),
        InlineKeyboardButton("⬅️ Asosiy menyu", callback_data="back_to_main")
    )
    return keyboard


def get_registration_keyboard():
    """Ro'yxatdan o'tish klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard


def get_regions_keyboard():
    """Hududlar klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    regions = Region.objects.all()

    for region in regions:
        keyboard.add(InlineKeyboardButton(
            text=region.name,
            callback_data=f"region_{region.id}"
        ))

    keyboard.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_registration"))
    return keyboard


def get_districts_keyboard(region_id):
    """Tumanlar klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    districts = District.objects.filter(region_id=region_id)

    for district in districts:
        keyboard.add(InlineKeyboardButton(
            text=district.name,
            callback_data=f"district_{district.id}"
        ))

    keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data=f"back_to_regions"))
    keyboard.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_registration"))
    return keyboard


def get_toifa_keyboard():
    """Toifa tanlash klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    for choice, label in TOIFA_CHOICES:
        keyboard.add(InlineKeyboardButton(
            text=label,
            callback_data=f"toifa_{choice}"
        ))

    keyboard.add(InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_registration"))
    return keyboard


def get_admin_decision_keyboard(teacher_id):
    """Admin qaror klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"accept_{teacher_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{teacher_id}")
    )
    return keyboard


def get_phone_keyboard():
    """Telefon raqam klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard


def get_profile_edit_keyboard():
    """Profil tahrirlash klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✏️ Ismni o'zgartirish", callback_data="edit_full_name"),
        InlineKeyboardButton("📱 Telefon raqamni o'zgartirish", callback_data="edit_phone")
    )
    keyboard.add(
        InlineKeyboardButton("🏛️ Hududni o'zgartirish", callback_data="edit_region"),
        InlineKeyboardButton("🏘️ Tumannni o'zgartirish", callback_data="edit_district")
    )
    keyboard.add(
        InlineKeyboardButton("🏫 Maktab nomini o'zgartirish", callback_data="edit_school"),
        InlineKeyboardButton("🏆 Toifani o'zgartirish", callback_data="edit_toifa")
    )
    keyboard.add(InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_profile"))
    return keyboard
