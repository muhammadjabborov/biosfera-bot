import logging
from aiogram import Bot
from aiogram.utils.deep_linking import get_start_link
from apps.bot.models import User, Teacher, Referral, Point, PointScore, LinkGot, ChannelID
from django.conf import settings
from django.db import models

# Simple cache for frequently accessed data
_point_threshold_cache = None
_point_threshold_cache_time = None

logger = logging.getLogger(__name__)


async def handle_referral(start_param, referee_user):
    """
    Handle referral when a user starts the bot with a referral parameter
    """
    if not start_param:
        return

    try:
        referrer_user_id = int(start_param)

        # Check if the referee is trying to refer themselves
        if referrer_user_id == referee_user.telegram_id:
            logger.warning(f"User {referee_user.telegram_id} attempted to refer themselves.")
            return

        # Optimize by fetching referrer with teacher info in one query
        referrer = User.objects.select_related('teacher').filter(telegram_id=referrer_user_id).first()
        if not referrer:
            logger.warning(f"Referrer not found for referral ID: {referrer_user_id}")
            return

        # Check if referrer is a confirmed teacher BEFORE creating referral
        if not hasattr(referrer, 'teacher') or not referrer.teacher.is_confirmed:
            logger.warning(f"Referrer {referrer_user_id} is not a confirmed teacher, referral not created")
            return

        # Check if referee already has a referral (only one referral per referee allowed)
        if Referral.objects.filter(referee=referee_user).exists():
            logger.info(f"Referee user already has a referral: {referee_user.telegram_id}")
            return

        # Check if referee is a confirmed teacher (only confirmed teachers can be referred)
        referee_teacher = Teacher.objects.filter(user=referee_user, is_confirmed=True).only('id').first()
        if referee_teacher:
            logger.warning(f"Referee {referee_user.telegram_id} is already a confirmed teacher, referral not created")
            return

        # Use get_or_create to prevent duplicates and handle race conditions
        referral, created = Referral.objects.get_or_create(
            referrer=referrer,
            referee=referee_user,
            defaults={}  # No additional fields to set
        )

        if created:
            logger.info(f"Referral created for confirmed teacher: {referral}")
        else:
            logger.info(f"Referral already exists from {referrer_user_id} to {referee_user.telegram_id}")

        # Don't increment points here - wait for teacher confirmation
        # Points will be given when the referee becomes a confirmed teacher

    except ValueError:
        logger.error(f"Invalid referral parameter: {start_param}")


async def check_and_send_invite_links(user, current_points):
    """
    Deprecated: Link distribution no longer depends on PointScore/points.
    Links are issued to the referee upon confirmation (see award_points_for_confirmed_teacher).
    This function is kept for backward compatibility and now does nothing.
    """
    logger.debug("check_and_send_invite_links is deprecated and is a no-op.")
    return


async def send_invite_links(user):
    """
    Send invite links to user based on channel IDs
    """
    try:
        channels = ChannelID.objects.only('channel_name', 'channel_id').all()
        if not channels:
            logger.warning("No channels configured for invite links")
            return

        message = "🎉 Tabriklaymiz! Siz quyidagi kanallarga taklif linklarini qo'lga kiritdingiz:\n\n"

        bot = Bot(token=settings.BOT_TOKEN)

        for channel in channels:
            try:
                # Create one-time invite link for the channel
                invite_link = await bot.create_chat_invite_link(
                    chat_id=channel.channel_id,
                    creates_join_request=False,
                    member_limit=1  # One-time use link
                )
                message += f"📢 {channel.channel_name}:\n{invite_link.invite_link}\n\n"
            except Exception as e:
                logger.error(f"Error generating invite link for channel {channel.channel_name}: {e}")
                message += f"📢 {channel.channel_name}: Xatolik yuz berdi\n\n"

        # Send message to user
        await bot.send_message(
            chat_id=user.telegram_id,
            text=message
        )
        
        # Close session properly
        session = await bot.get_session()
        await session.close()

    except Exception as e:
        logger.error(f"Error sending invite links to user {user.telegram_id}: {e}")


def get_user_points(user):
    """
    Get total points for a user
    """
    point = Point.objects.filter(user=user).only('points').first()
    return point.points if point else 0


def get_user_referrals(user):
    """
    Get number of successful referrals for a user (only confirmed teachers)
    """
    return Referral.objects.filter(
        referrer=user,
        referee__teacher__is_confirmed=True
    ).only('id').count()


def get_user_referrals_by_region(user):
    """
    Get number of successful referrals by region for a user
    """
    return Referral.objects.filter(
        referrer=user,
        referee__teacher__is_confirmed=True
    ).values('referee__teacher__region__name').annotate(
        count=models.Count('id')
    ).order_by('-count')


def get_user_referrals_by_district(user):
    """
    Get number of successful referrals by district for a user
    """
    return Referral.objects.filter(
        referrer=user,
        referee__teacher__is_confirmed=True
    ).values('referee__teacher__district__name').annotate(
        count=models.Count('id')
    ).order_by('-count')


def get_total_referrals_stats():
    """
    Get total statistics for all referrals
    """
    total_referrals = Referral.objects.filter(
        referee__teacher__is_confirmed=True
    ).count()

    total_by_region = Referral.objects.filter(
        referee__teacher__is_confirmed=True
    ).values('referee__teacher__region__name').annotate(
        count=models.Count('id')
    ).order_by('-count')

    total_by_district = Referral.objects.filter(
        referee__teacher__is_confirmed=True
    ).values('referee__teacher__district__name').annotate(
        count=models.Count('id')
    ).order_by('-count')

    return {
        'total': total_referrals,
        'by_region': total_by_region,
        'by_district': total_by_district
    }


async def generate_referral_link(user):
    """
    Generate referral link for a user
    """
    try:
        bot = Bot(token=settings.BOT_TOKEN)
        bot_info = await bot.get_me()
        
        # Close session properly
        session = await bot.get_session()
        await session.close()
        
        return f"https://t.me/{bot_info.username}?start={user.telegram_id}"
    except Exception as e:
        logger.error(f"Error generating referral link: {e}")
        return f"https://t.me/bot?start={user.telegram_id}"


async def award_points_for_confirmed_teacher(teacher_user):
    """
    When a referred teacher gets confirmed:
    - Increment ONE point for each referrer who invited this teacher
    - Send invite links to the CONFIRMED referee (the one who started via referral)
      exactly once
    """
    try:
        # Find referrals where this user was the referee - optimize with select_related
        referrals = Referral.objects.select_related('referrer__teacher').filter(referee=teacher_user)

        # 1) Award points to referrers (do NOT send links to referrer)
        for referral in referrals:
            referrer = referral.referrer

            # Check if referrer is still a confirmed teacher - use cached data
            if hasattr(referrer, 'teacher') and referrer.teacher.is_confirmed:
                # Increment points for referrer
                point, created = Point.objects.get_or_create(
                    user=referrer,
                    defaults={'points': 1}
                )
                if not created:
                    point.points += 1
                    point.save()

                logger.info(f"Points awarded to referrer {referrer} for confirmed teacher {teacher_user}: {point}")
            else:
                logger.warning(f"Referrer {referrer} is no longer a confirmed teacher, no points awarded")

        # 2) Send invite links to the CONFIRMED referee if they started via referral
        if referrals.exists():
            link_got, created = LinkGot.objects.get_or_create(user=teacher_user, defaults={'is_get': False})
            if not link_got.is_get:
                await send_invite_links(teacher_user)
                link_got.is_get = True
                link_got.save()
                logger.info(f"Invite links sent to confirmed referee: {teacher_user.telegram_id}")

    except Exception as e:
        logger.error(f"Error awarding points for confirmed teacher {teacher_user}: {e}")
