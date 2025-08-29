from django.contrib import admin

from apps.common.models import Region, District


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "region")
    search_fields = ("name",)
    list_filter = ("region",)
