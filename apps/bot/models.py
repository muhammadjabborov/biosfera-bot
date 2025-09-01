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


class ChannelID(BaseModel):
    channel_name = models.CharField(max_length=255)
    channel_id = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Channel ID'
        verbose_name_plural = 'Channel IDs'


class MessageID(BaseModel):
    message_id = models.BigIntegerField()


class Point(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.user} - {self.points}'

    class Meta:
        verbose_name = 'Point'
        verbose_name_plural = 'Points'


class PointScore(BaseModel):
    points = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.points}'

    class Meta:
        verbose_name = 'PointScore'
        verbose_name_plural = 'PointScores'


class LinkGot(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_get = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user} - {self.is_get}'

    class Meta:
        verbose_name = 'LinkGot'
        verbose_name_plural = 'LinkGots'


class Referral(BaseModel):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referrer')
    referee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referee')

    def __str__(self):
        return f'{self.referrer} - {self.referee}'

    class Meta:
        verbose_name = 'Referral'
        verbose_name_plural = 'Referrals'
        unique_together = ['referrer', 'referee']  # Prevent duplicate referrals