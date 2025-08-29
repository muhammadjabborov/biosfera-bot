from apps.common.models import BaseModel
from django.db import models
from django.utils.translation import gettext_lazy as _

TOIFA_CHOICES = [
    ('oliy', 'Oliy'),
    ('1', '1-toifa'),
    ('2', '2-toifa'),
    ('mutaxassis', 'Mutaxassis'),
    ('yoq', 'Yo\'q'),
]


class User(BaseModel):
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)
    telegram_id = models.BigIntegerField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.telegram_id})"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class Teacher(BaseModel):
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='teacher')
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    region = models.ForeignKey('common.Region', on_delete=models.CASCADE)
    district = models.ForeignKey('common.District', on_delete=models.CASCADE)
    address = models.CharField(max_length=255, blank=True, null=True)
    school_name = models.CharField(max_length=255)
    toifa = models.CharField(max_length=20, choices=TOIFA_CHOICES, default='yoq')
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = 'Teacher Profile'
        verbose_name_plural = 'Teacher Profiles'


class MessageID(BaseModel):
    message_id = models.BigIntegerField()
