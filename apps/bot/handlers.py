import os
import django
from apps.bot.config import bot, dp
from django.conf import settings
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from apps.bot.models import User, Teacher, TOIFA_CHOICES
from apps.bot.keyboards import (
    get_main_keyboard, get_registered_user_keyboard, get_registration_keyboard, get_regions_keyboard,
    get_districts_keyboard, get_toifa_keyboard, get_admin_decision_keyboard,
    get_phone_keyboard, get_profile_edit_keyboard
)
from apps.common.models import Region, District
import logging

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

django.setup()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RegistrationStates(StatesGroup):
    full_name = State()
    phone_number = State()
    region = State()
    district = State()
    school_name = State()
    toifa = State()
    toifa_document = State()


class ProfileEditStates(StatesGroup):
    full_name = State()
    phone_number = State()
    region = State()
    district = State()
    school_name = State()
    toifa = State()


@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    # Extract start parameter for referral
    start_param = None
    if message.get_args():
        start_param = message.get_args()

    user, created = User.objects.get_or_create(
        telegram_id=message.from_user.id,
        defaults={'username': message.from_user.username}
    )

    # Handle referral if start parameter exists
    if start_param:
        from apps.bot.utils import handle_referral
        await handle_referral(start_param, user)

    teacher = (
        Teacher.objects
        .only('is_confirmed', 'id')  # keep it light
        .filter(user=user)
        .first()
    )

    if teacher:
        if teacher.is_confirmed:
            await message.answer(
                "🎉 Xush kelibsiz! Siz tasdiqlangan o'qituvchisiz!\n\n"
                "Quyidagi imkoniyatlardan foydalanishingiz mumkin:",
                reply_markup=get_registered_user_keyboard()
            )
        else:
            await message.answer(
                "⏳ Sizning arizangiz hali ko'rib chiqilmoqda.\n"
                "Natijani kutib turing yoki ma'lumotlaringizni yangilang.",
                reply_markup=get_main_keyboard()
            )
    else:
        await message.answer(
            "👋 Xush kelibsiz!\n\n"
            "O'qituvchi sifatida ro'yxatdan o'tish uchun quyidagi tugmani bosing:",
            reply_markup=get_main_keyboard()
        )


@dp.message_handler(text="🔗 Referal")
async def show_referral(message: types.Message):
    """Referal ma'lumotlarini ko'rsatish"""
    from apps.bot.utils import get_user_referrals, generate_referral_link

    # Use select_related to optimize the query
    user = User.objects.select_related('teacher').get(telegram_id=message.from_user.id)
    referral_count = get_user_referrals(user)
    referral_link = await generate_referral_link(user)

    await message.answer(
        f"🔗 Referal tizimi\n\n"
        f"📊 Sizning referallaringiz: {referral_count}\n"
        f"🔗 Sizning referal havolangiz:\n{referral_link}\n\n"
        f"Do'stlaringizni taklif qiling va ballar qo'shing!"
    )


@dp.message_handler(text="🏆 Mening ballarim")
async def show_points(message: types.Message):
    """Foydalanuvchi ballarini ko'rsatish"""
    from apps.bot.utils import get_user_points, get_user_referrals
    from apps.bot.models import PointScore, LinkGot
    from apps.bot.keyboards import get_statistics_keyboard

    # Optimize queries by fetching user and related data in one go
    user = User.objects.select_related('teacher').get(telegram_id=message.from_user.id)

    # Get basic user data
    points = get_user_points(user)
    referral_count = get_user_referrals(user)

    # Get point threshold - use cached value from utils
    from apps.bot.utils import _point_threshold_cache, _point_threshold_cache_time
    import time

    current_time = time.time()
    if (_point_threshold_cache is None or
            _point_threshold_cache_time is None or
            current_time - _point_threshold_cache_time > 300):  # 5 minutes cache

        point_score = PointScore.objects.only('points').first()
        threshold = point_score.points if point_score else 5
    else:
        threshold = _point_threshold_cache

    link_got = LinkGot.objects.filter(user=user, is_get=True).only('id').first()
    link_status = "✅ Qo'lga kiritilgan" if link_got else "❌ Hali qo'lga kiritilmagan"

    # Build basic statistics message
    stats_message = f"📊 Statistika\n\n"
    stats_message += f"Jami ball: {points}\n"
    stats_message += f"Qaysi darajada statistikani ko'rmoqchisiz?"

    await message.answer(stats_message, reply_markup=get_statistics_keyboard())


@dp.callback_query_handler(lambda c: c.data == "stats_district")
async def show_district_stats(callback_query: types.CallbackQuery):
    """Tuman bo'yicha statistika"""
    from apps.bot.utils import get_user_referrals_by_district, get_total_referrals_stats
    from apps.bot.keyboards import get_statistics_keyboard

    user = User.objects.select_related('teacher').get(telegram_id=callback_query.from_user.id)
    user_district_stats = get_user_referrals_by_district(user)
    total_stats = get_total_referrals_stats()

    message = "🏘️ Tuman bo'yicha statistika\n\n"

    if user_district_stats:
        message += "Sizning tumanlaringiz:\n"
        for stat in user_district_stats:
            message += f"• {stat['referee__teacher__district__name']}: {stat['count']}\n"
        message += "\n"

    if total_stats['by_district']:
        message += "Umumiy tumanlar:\n"
        for stat in total_stats['by_district']:
            message += f"• {stat['referee__teacher__district__name']}: {stat['count']}\n"

    await callback_query.message.edit_text(message, reply_markup=get_statistics_keyboard())
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == "stats_region")
async def show_region_stats(callback_query: types.CallbackQuery):
    """Viloyat bo'yicha statistika"""
    from apps.bot.utils import get_user_referrals_by_region, get_total_referrals_stats
    from apps.bot.keyboards import get_statistics_keyboard

    user = User.objects.select_related('teacher').get(telegram_id=callback_query.from_user.id)
    user_region_stats = get_user_referrals_by_region(user)
    total_stats = get_total_referrals_stats()

    message = "🏛️ Viloyat bo'yicha statistika\n\n"

    if user_region_stats:
        message += "Sizning viloyatlaringiz:\n"
        for stat in user_region_stats:
            message += f"• {stat['referee__teacher__region__name']}: {stat['count']}\n"
        message += "\n"

    if total_stats['by_region']:
        message += "Umumiy viloyatlar:\n"
        for stat in total_stats['by_region']:
            message += f"• {stat['referee__teacher__region__name']}: {stat['count']}\n"

    await callback_query.message.edit_text(message, reply_markup=get_statistics_keyboard())
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == "stats_republic")
async def show_republic_stats(callback_query: types.CallbackQuery):
    """Respublika bo'yicha statistika"""
    from apps.bot.utils import get_user_points, get_user_referrals, get_total_referrals_stats
    from apps.bot.models import PointScore, LinkGot
    from apps.bot.keyboards import get_statistics_keyboard

    user = User.objects.select_related('teacher').get(telegram_id=callback_query.from_user.id)
    points = get_user_points(user)
    referral_count = get_user_referrals(user)
    total_stats = get_total_referrals_stats()

    # Get point threshold
    from apps.bot.utils import _point_threshold_cache, _point_threshold_cache_time
    import time

    current_time = time.time()
    if (_point_threshold_cache is None or
            _point_threshold_cache_time is None or
            current_time - _point_threshold_cache_time > 300):

        point_score = PointScore.objects.only('points').first()
        threshold = point_score.points if point_score else 5
    else:
        threshold = _point_threshold_cache

    link_got = LinkGot.objects.filter(user=user, is_get=True).only('id').first()
    link_status = "✅ Qo'lga kiritilgan" if link_got else "❌ Hali qo'lga kiritilmagan"

    message = "🇺🇿 Respublika bo'yicha statistika\n\n"
    message += f"Jami ball: {points}\n"
    message += f"Sizning referallaringiz: {referral_count}\n"
    message += f"Ballar chegarasi: {threshold}\n"
    message += f"Taklif linklari: {link_status}\n\n"
    message += f"Umumiy tasdiqlangan o'qituvchilar: {total_stats['total']}"

    await callback_query.message.edit_text(message, reply_markup=get_statistics_keyboard())
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == "back_to_main")
async def back_to_main_menu(callback_query: types.CallbackQuery):
    """Asosiy menyuga qaytish"""
    await callback_query.message.edit_text("Asosiy menyuga qaytdingiz.")
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="Quyidagi imkoniyatlardan foydalanishingiz mumkin:",
        reply_markup=get_registered_user_keyboard()
    )
    await callback_query.answer()


@dp.message_handler(text="👤 Profil")
async def show_profile(message: types.Message):
    """Profil ma'lumotlarini ko'rsatish"""
    # Grab the Teacher directly and pull relateds in one go
    teacher = (
        Teacher.objects
        .select_related('user', 'region', 'district')
        .filter(user__telegram_id=message.from_user.id)
        .only(
            'full_name', 'phone_number', 'school_name', 'toifa', 'is_confirmed',
            'region__name', 'district__name', 'user__telegram_id'
        )
        .first()
    )

    if teacher:
        toifa_label = dict(TOIFA_CHOICES).get(teacher.toifa, teacher.toifa)
        status = "✅ Tasdiqlangan" if teacher.is_confirmed else "⏳ Ko'rib chiqilmoqda"

        await message.answer(
            f"👤 Sizning profilingiz\n\n"
            f"📝 To'liq ism: {teacher.full_name}\n"
            f"📱 Telefon: {teacher.phone_number}\n"
            f"🏛️ Hudud: {teacher.region.name}\n"
            f"🏘️ Tuman: {teacher.district.name}\n"
            f"🏫 Maktab: {teacher.school_name}\n"
            f"🏆 Toifa: {toifa_label}\n"
            f"📊 Holat: {status}\n\n"
            f"Ma'lumotlaringizni tahrirlash uchun quyidagi tugmalardan birini bosing:",
            reply_markup=get_profile_edit_keyboard()
        )
    else:
        await message.answer(
            "❌ Sizda hali o'qituvchi profili mavjud emas.\n"
            "📝 Ro'yxatdan o'tish tugmasini bosing.",
            reply_markup=get_main_keyboard()
        )


@dp.callback_query_handler(lambda c: c.data == "back_to_profile")
async def back_to_profile(callback_query: types.CallbackQuery):
    """Profilga qaytish"""
    await show_profile(callback_query.message)
    await callback_query.answer()


@dp.callback_query_handler(lambda c: c.data == "edit_full_name")
async def edit_full_name_start(callback_query: types.CallbackQuery):
    """Ismni tahrirlashni boshlash"""
    await callback_query.message.edit_text(
        "✏️ Yangi to'liq ismingizni kiriting:"
    )
    await ProfileEditStates.full_name.set()


@dp.message_handler(state=ProfileEditStates.full_name)
async def edit_full_name_process(message: types.Message, state: FSMContext):
    if len(message.text) < 3:
        await message.answer("❌ Ism juda qisqa. Iltimos, to'liq ismingizni kiriting:")
        return

    Teacher.objects.filter(user__telegram_id=message.from_user.id).update(full_name=message.text)

    await state.finish()
    await message.answer(
        f"✅ Ismingiz muvaffaqiyatli o'zgartirildi: {message.text}",
        reply_markup=get_registered_user_keyboard()
    )


@dp.callback_query_handler(lambda c: c.data == "edit_phone")
async def edit_phone_start(callback_query: types.CallbackQuery):
    """Telefon raqamni tahrirlashni boshlash"""
    await callback_query.message.edit_text(
        "📱 Yangi telefon raqamingizni kiriting yoki tugmani bosing:",
        reply_markup=get_phone_keyboard()
    )
    await ProfileEditStates.phone_number.set()


@dp.message_handler(content_types=['contact', 'text'], state=ProfileEditStates.phone_number)
async def edit_phone_process(message: types.Message, state: FSMContext):
    """Telefon raqamni tahrirlash"""
    if message.text == "❌ Bekor qilish":
        await state.finish()
        await message.answer(
            "❌ Tahrirlash bekor qilindi.",
            reply_markup=get_registered_user_keyboard()
        )
        return

    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
    elif message.text and message.text.startswith('+'):
        phone_number = message.text
    elif message.text and message.text.isdigit():
        phone_number = '+998' + message.text[-9:] if len(message.text) == 9 else message.text

    if not phone_number:
        await message.answer("❌ Iltimos, to'g'ri telefon raqam kiriting:")
        return

    Teacher.objects.filter(user__telegram_id=message.from_user.id).update(phone_number=phone_number)

    await state.finish()
    await message.answer(
        f"✅ Telefon raqamingiz muvaffaqiyatli o'zgartirildi: {phone_number}",
        reply_markup=get_registered_user_keyboard()
    )


@dp.callback_query_handler(lambda c: c.data == "edit_region")
async def edit_region_start(callback_query: types.CallbackQuery):
    """Hududni tahrirlashni boshlash"""
    await callback_query.message.edit_text(
        "🏛️ Yangi hududingizni tanlang:",
        reply_markup=get_regions_keyboard()
    )
    await ProfileEditStates.region.set()


@dp.callback_query_handler(lambda c: c.data.startswith('region_'), state=ProfileEditStates.region)
async def edit_region_process(callback_query: types.CallbackQuery, state: FSMContext):
    """Hududni tahrirlash"""
    region_id = int(callback_query.data.split('_')[1])

    await state.update_data(region_id=region_id)

    await callback_query.message.edit_text(
        f"🏛️ {Region.objects.get(id=region_id).name} hududi tanlandi.\n\n"
        "🏘️ Yangi tumaningizni tanlang:",
        reply_markup=get_districts_keyboard(region_id)
    )
    await ProfileEditStates.district.set()


@dp.callback_query_handler(lambda c: c.data.startswith('district_'), state=ProfileEditStates.district)
async def edit_district_process(callback_query: types.CallbackQuery, state: FSMContext):
    district_id = int(callback_query.data.split('_')[1])
    data = await state.get_data()
    region_id = data['region_id']

    Teacher.objects.filter(user__telegram_id=str(callback_query.from_user.id)).update(
        region_id=region_id,
        district_id=district_id
    )

    region_name = Region.objects.only('name').get(id=region_id).name
    district_name = District.objects.only('name').get(id=district_id).name

    await state.finish()
    await callback_query.message.edit_text(
        f"✅ Hudud va tumaningiz muvaffaqiyatli o'zgartirildi:\n"
        f"🏛️ {region_name}\n"
        f"🏘️ {district_name}"
    )
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="Profilga qaytish uchun 👤 Profil tugmasini bosing.",
        reply_markup=get_registered_user_keyboard()
    )


@dp.callback_query_handler(lambda c: c.data == "edit_school")
async def edit_school_start(callback_query: types.CallbackQuery):
    """Maktab nomini tahrirlashni boshlash"""
    await callback_query.message.edit_text(
        "🏫 Yangi maktab nomini kiriting:"
    )
    await ProfileEditStates.school_name.set()


@dp.message_handler(state=ProfileEditStates.school_name)
async def edit_school_process(message: types.Message, state: FSMContext):
    """Maktab nomini tahrirlash"""
    if len(message.text) < 3:
        await message.answer("❌ Maktab nomi juda qisqa. Iltimos, to'liq nomini kiriting:")
        return

    # Optimize by using select_related and update instead of get + save
    Teacher.objects.filter(user__telegram_id=message.from_user.id).update(school_name=message.text)

    await state.finish()
    await message.answer(
        f"✅ Maktab nomingiz muvaffaqiyatli o'zgartirildi: {message.text}",
        reply_markup=get_registered_user_keyboard()
    )


@dp.callback_query_handler(lambda c: c.data == "edit_toifa")
async def edit_toifa_start(callback_query: types.CallbackQuery):
    """Toifani tahrirlashni boshlash"""
    await callback_query.message.edit_text(
        "🏆 Yangi o'qituvchilik toifangizni tanlang:",
        reply_markup=get_toifa_keyboard()
    )
    await ProfileEditStates.toifa.set()


@dp.callback_query_handler(lambda c: c.data.startswith('toifa_'), state=ProfileEditStates.toifa)
async def edit_toifa_process(callback_query: types.CallbackQuery, state: FSMContext):
    """Toifani tahrirlash"""
    toifa = callback_query.data.split('_')[1]
    toifa_label = dict(TOIFA_CHOICES)[toifa]

    # Optimize by using update instead of get + save
    Teacher.objects.filter(user__telegram_id=str(callback_query.from_user.id)).update(toifa=toifa)

    await state.finish()
    await callback_query.message.edit_text(
        f"✅ Toifangiz muvaffaqiyatli o'zgartirildi: {toifa_label}"
    )
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="Profilga qaytish uchun 👤 Profil tugmasini bosing.",
        reply_markup=get_registered_user_keyboard()
    )


@dp.message_handler(text="📝 Ro'yxatdan o'tish")
async def start_registration(message: types.Message):
    """Ro'yxatdan o'tishni boshlash"""
    # Optimize by using select_related to fetch user with teacher in one query
    user = User.objects.select_related('teacher').filter(telegram_id=message.from_user.id).first()

    # Check if user already has a teacher profile
    if user and hasattr(user, 'teacher') and user.teacher:
        if user.teacher.is_confirmed:
            await message.answer(
                "✅ Siz allaqachon tasdiqlangan o'qituvchisiz!\n"
                "Ma'lumotlaringizni yangilash uchun 👤 Profil tugmasini bosing.",
                reply_markup=get_registered_user_keyboard()
            )
            return
        else:
            # Update existing profile
            await message.answer(
                "🔄 Mavjud arizangizni yangilash.\n"
                "To'liq ismingizni kiriting:"
            )
            await RegistrationStates.full_name.set()
            return

    await message.answer(
        "📝 O'qituvchi sifatida ro'yxatdan o'tish\n\n"
        "To'liq ismingizni kiriting:",
        reply_markup=get_registration_keyboard()
    )
    await RegistrationStates.full_name.set()


@dp.message_handler(text="❌ Bekor qilish", state="*")
async def cancel_registration_handler(message: types.Message, state: FSMContext):
    """Ro'yxatdan o'tishni bekor qilish"""
    await state.finish()
    await message.answer(
        "❌ Ro'yxatdan o'tish bekor qilindi.",
        reply_markup=get_main_keyboard()
    )


@dp.message_handler(state=RegistrationStates.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    """To'liq ismni qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await cancel_registration_handler(message, state)
        return

    if len(message.text) < 3:
        await message.answer("❌ Ism juda qisqa. Iltimos, to'liq ismingizni kiriting:")
        return

    # Store full name in state data
    await state.update_data(full_name=message.text)

    await message.answer(
        "📱 Telefon raqamingizni kiriting yoki tugmani bosing:",
        reply_markup=get_phone_keyboard()
    )
    await RegistrationStates.phone_number.set()


@dp.message_handler(content_types=['contact', 'text'], state=RegistrationStates.phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    """Telefon raqamni qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await cancel_registration_handler(message, state)
        return

    phone_number = None
    if message.contact:
        phone_number = message.contact.phone_number
    elif message.text and message.text.startswith('+'):
        phone_number = message.text
    elif message.text and message.text.isdigit():
        phone_number = '+998' + message.text[-9:] if len(message.text) == 9 else message.text

    if not phone_number:
        await message.answer("❌ Iltimos, to'g'ri telefon raqam kiriting:")
        return

    # Store phone number in state data
    await state.update_data(phone_number=phone_number)

    await message.answer(
        "🏛️ Hududingizni tanlang:",
        reply_markup=get_regions_keyboard()
    )
    await RegistrationStates.region.set()


@dp.callback_query_handler(lambda c: c.data.startswith('region_'), state=RegistrationStates.region)
async def process_region_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Hudud tanlashini qabul qilish"""
    region_id = int(callback_query.data.split('_')[1])

    # Store region_id in state data
    await state.update_data(region_id=region_id)

    await callback_query.message.edit_text(
        f"🏛️ {Region.objects.get(id=region_id).name} hududi tanlandi.\n\n"
        "🏘️ Tumaningizni tanlang:",
        reply_markup=get_districts_keyboard(region_id)
    )
    await RegistrationStates.district.set()


@dp.callback_query_handler(lambda c: c.data.startswith('district_'), state=RegistrationStates.district)
async def process_district_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Tuman tanlashini qabul qilish"""
    district_id = int(callback_query.data.split('_')[1])

    # Store district_id in state data
    await state.update_data(district_id=district_id)

    district = District.objects.get(id=district_id)
    await callback_query.message.edit_text(
        f"🏘️ {district.name} tumani tanlandi.\n\n"
        "🏫 Maktabingizning nomini kiriting:"
    )
    await RegistrationStates.school_name.set()


@dp.callback_query_handler(lambda c: c.data == 'back_to_regions', state=RegistrationStates.district)
async def back_to_regions(callback_query: types.CallbackQuery, state: FSMContext):
    """Hududlarga qaytish"""
    await callback_query.message.edit_text(
        "🏛️ Hududingizni tanlang:",
        reply_markup=get_regions_keyboard()
    )
    await RegistrationStates.region.set()


@dp.message_handler(state=RegistrationStates.school_name)
async def process_school_name(message: types.Message, state: FSMContext):
    """Maktab nomini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await cancel_registration_handler(message, state)
        return

    if len(message.text) < 3:
        await message.answer("❌ Maktab nomi juda qisqa. Iltimos, to'liq nomini kiriting:")
        return

    # Store school name in state data
    await state.update_data(school_name=message.text)

    await message.answer(
        "🏆 O'qituvchilik toifangizni tanlang:",
        reply_markup=get_toifa_keyboard()
    )
    await RegistrationStates.toifa.set()


@dp.callback_query_handler(lambda c: c.data.startswith('toifa_'), state=RegistrationStates.toifa)
async def process_toifa_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Toifa tanlashini qabul qilish"""
    toifa = callback_query.data.split('_')[1]

    # Store toifa in state data
    await state.update_data(toifa=toifa)

    toifa_label = dict(TOIFA_CHOICES)[toifa]

    if toifa == 'yoq':
        # No document needed, complete registration
        await complete_registration(callback_query.message, callback_query.from_user.id, state)
    else:
        await callback_query.message.edit_text(
            f"🏆 {toifa_label} toifasi tanlandi.\n\n"
            "📄 Toifa hujjatini yuboring (PDF, rasm yoki boshqa format):"
        )
        await RegistrationStates.toifa_document.set()


@dp.message_handler(content_types=['document', 'photo'], state=RegistrationStates.toifa_document)
async def process_toifa_document(message: types.Message, state: FSMContext):
    """Toifa hujjatini qabul qilish"""
    if message.text == "❌ Bekor qilish":
        await cancel_registration_handler(message, state)
        return

    # Complete registration with document
    await complete_registration_with_document(message, message.from_user.id, state)


async def complete_registration_with_document(message, user_id, state):
    try:
        data = await state.get_data()
        user = User.objects.only('id', 'telegram_id').get(telegram_id=str(user_id))

        teacher, _ = Teacher.objects.update_or_create(
            user=user,
            defaults={
                'full_name': data['full_name'],
                'phone_number': data['phone_number'],
                'region_id': data['region_id'],
                'district_id': data['district_id'],
                'school_name': data['school_name'],
                'toifa': data['toifa'],
                'is_confirmed': False,
            }
        )

        if settings.CHAT_ID:
            await send_to_admin_channel_with_document(teacher, data, message)
            await message.answer(
                "✅ Arizangiz muvaffaqiyatli yuborildi!\n\n"
                "📋 Yuborilgan ma'lumotlar:\n"
                f"👤 To'liq ism: {data['full_name']}\n"
                f"📱 Telefon: {data['phone_number']}\n"
                f"🏫 Maktab: {data['school_name']}\n"
                f"🏆 Toifa: {dict(TOIFA_CHOICES)[data['toifa']]}\n\n"
                "⏳ Admin tomonidan ko'rib chiqilgandan so'ng sizga xabar beriladi.",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Admin kanali sozlanmagan. Iltimos, admin bilan bog'laning.",
                reply_markup=get_main_keyboard()
            )

        await state.finish()

    except Exception as e:
        logger.error(f"Error completing registration: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.", reply_markup=get_main_keyboard())


async def send_to_admin_channel_with_document(teacher, data, message):
    try:
        # Use values fetched once
        region_name = Region.objects.only('name').get(id=data['region_id']).name
        district_name = District.objects.only('name').get(id=data['district_id']).name
        toifa_label = dict(TOIFA_CHOICES)[data['toifa']]

        caption = (
            f"📝 Yangi o'qituvchi arizasi\n\n"
            f"👤 To'liq ism: {data['full_name']}\n"
            f"📱 Telefon: {data['phone_number']}\n"
            f"🏛️ Hudud: {region_name}\n"
            f"🏘️ Tuman: {district_name}\n"
            f"🏫 Maktab: {data['school_name']}\n"
            f"🏆 Toifa: {toifa_label}\n"
            f"🆔 ID: {teacher.id}"
        )

        if message.document:
            await bot.send_document(
                chat_id=settings.CHAT_ID,
                document=message.document.file_id,
                caption=caption,
                reply_markup=get_admin_decision_keyboard(teacher.id)
            )
        elif message.photo:
            await bot.send_photo(
                chat_id=settings.CHAT_ID,
                photo=message.photo[-1].file_id,
                caption=caption,
                reply_markup=get_admin_decision_keyboard(teacher.id)
            )
    except Exception as e:
        logger.error(f"Error sending to admin channel: {e}")


async def complete_registration(message, user_id, state):
    try:
        data = await state.get_data()
        user = User.objects.only('id').get(telegram_id=str(user_id))

        teacher, created = Teacher.objects.update_or_create(
            user=user,
            defaults={
                'full_name': data['full_name'],
                'phone_number': data['phone_number'],
                'region_id': data['region_id'],
                'district_id': data['district_id'],
                'school_name': data['school_name'],
                'toifa': data['toifa'],
                'is_confirmed': True,  # auto-confirm
            }
        )

        # Award points to referrer if this teacher was referred
        from apps.bot.utils import award_points_for_confirmed_teacher
        await award_points_for_confirmed_teacher(teacher.user)

        await message.answer(
            "🎉 Tabriklaymiz! Siz muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
            "📋 Ma'lumotlaringiz:\n"
            f"👤 To'liq ism: {data['full_name']}\n"
            f"📱 Telefon: {data['phone_number']}\n"
            f"🏫 Maktab: {data['school_name']}\n"
            f"🏆 Toifa: {dict(TOIFA_CHOICES)[data['toifa']]}\n\n"
            "Endi siz quyidagi imkoniyatlardan foydalanishingiz mumkin:",
            reply_markup=get_registered_user_keyboard()
        )
        await state.finish()

    except Exception as e:
        logger.error(f"Error completing registration: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.", reply_markup=get_main_keyboard())


@dp.callback_query_handler(lambda c: c.data.startswith('accept_'))
async def accept_teacher(callback_query: types.CallbackQuery):
    teacher_id = int(callback_query.data.split('_')[1])
    try:
        teacher = Teacher.objects.select_related('user').get(id=teacher_id)
        Teacher.objects.filter(id=teacher_id).update(is_confirmed=True)  # single UPDATE

        # Award points to referrer if this teacher was referred
        from apps.bot.utils import award_points_for_confirmed_teacher
        await award_points_for_confirmed_teacher(teacher.user)

        # Try editing the original admin message
        try:
            if callback_query.message.text:
                await callback_query.message.edit_text(f"{callback_query.message.text}\n\n✅ TASDIQLANDI")
            elif callback_query.message.caption:
                await callback_query.message.edit_caption(f"{callback_query.message.caption}\n\n✅ TASDIQLANDI")
            else:
                await callback_query.message.answer(f"✅ O'qituvchi ID: {teacher_id} tasdiqlandi!")
        except Exception as e:
            logger.error(f"Error editing admin message: {e}")
            await callback_query.message.answer(f"✅ O'qituvchi ID: {teacher_id} tasdiqlandi!")

        await bot.send_message(
            chat_id=teacher.user.telegram_id,
            text="🎉 Tabriklaymiz! Sizning arizangiz tasdiqlandi!\n\n"
                 "Endi siz quyidagi imkoniyatlardan foydalanishingiz mumkin:",
            reply_markup=get_registered_user_keyboard()
        )
    except Exception as e:
        logger.error(f"Error accepting teacher: {e}")
        await callback_query.answer("❌ Xatolik yuz berdi")


@dp.callback_query_handler(lambda c: c.data.startswith('reject_'))
async def reject_teacher(callback_query: types.CallbackQuery):
    teacher_id = int(callback_query.data.split('_')[1])
    try:
        teacher = Teacher.objects.select_related('user').get(id=teacher_id)
        user_tid = teacher.user.telegram_id  # cache before delete
        teacher.delete()

        try:
            if callback_query.message.text:
                await callback_query.message.edit_text(f"{callback_query.message.text}\n\n❌ RAD ETILDI")
            elif callback_query.message.caption:
                await callback_query.message.edit_caption(f"{callback_query.message.caption}\n\n❌ RAD ETILDI")
            else:
                await callback_query.message.answer(f"❌ O'qituvchi ID: {teacher_id} rad etildi!")
        except Exception as e:
            logger.error(f"Error editing admin message: {e}")
            await callback_query.message.answer(f"❌ O'qituvchi ID: {teacher_id} rad etildi!")

        await bot.send_message(
            chat_id=user_tid,
            text="❌ Kechirasiz, sizning arizangiz rad etildi.\n\n"
                 "Iltimos, ma'lumotlaringizni tekshirib, qaytadan ariza bering.",
            reply_markup=get_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Error rejecting teacher: {e}")
        await callback_query.answer("❌ Xatolik yuz berdi")


@dp.callback_query_handler(lambda c: c.data == "cancel_registration")
async def cancel_registration_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Ro'yxatdan o'tishni bekor qilish (callback)"""
    await state.finish()
    await callback_query.message.edit_text("❌ Ro'yxatdan o'tish bekor qilindi.")
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text="Asosiy menyuga qaytdingiz.",
        reply_markup=get_main_keyboard()
    )


# Error handler
@dp.errors_handler()
async def errors_handler(update, exception):
    """Xatolarni qayta ishlash"""
    logger.error(f"Update: {update}\nException: {exception}")
    return True
