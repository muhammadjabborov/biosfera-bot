from django.contrib import admin
from .models import User, Teacher, Point, PointScore, LinkGot, Referral, ChannelID


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'telegram_id')
    search_fields = ('telegram_id',)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'user', 'phone_number', 'region', 'district', 'school_name', 'toifa')
    search_fields = ('full_name', 'school_name')
    list_filter = ('region', 'district')
    fieldsets = (
        (None, {
            'fields': (
                'user', 'full_name', 'phone_number', 'region', 'district', 'address', 'school_name', 'toifa')
        }),
    )


@admin.register(Point)
class PointAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'created_at')
    search_fields = ('user__username', 'user__telegram_id')
    list_filter = ('created_at',)


@admin.register(PointScore)
class PointScoreAdmin(admin.ModelAdmin):
    list_display = ('points', 'created_at')


@admin.register(LinkGot)
class LinkGotAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_get', 'created_at')
    search_fields = ('user__username', 'user__telegram_id')
    list_filter = ('is_get', 'created_at')


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referee', 'created_at')
    search_fields = ('referrer__username', 'referee__username')
    list_filter = ('created_at',)


@admin.register(ChannelID)
class ChannelIDAdmin(admin.ModelAdmin):
    list_display = ('channel_name', 'channel_id', 'created_at')
    search_fields = ('channel_name', 'channel_id')
