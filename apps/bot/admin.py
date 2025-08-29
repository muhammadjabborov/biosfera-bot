from django.contrib import admin
from .models import User, Teacher


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
