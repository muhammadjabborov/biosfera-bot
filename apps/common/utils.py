import os
import json
from django.conf import settings
from django.db import IntegrityError

from apps.common.models import Region, District


def load_regions():
    with open(os.path.join(settings.BASE_DIR, 'apps/common/data/regions.json'), encoding="utf8",
              errors='ignore') as json_file:
        data = json.load(json_file)
        for region in data:
            try:
                Region.objects.create(id=region['id'], name=region['name'])
            except IntegrityError:
                region_obj = Region.objects.get(id=region['id'])
                region_obj.name = region['name']
                region_obj.save()
        return Region.objects.all()


def load_districts():
    with open(os.path.join(settings.BASE_DIR, 'apps/common/data/districts.json'), encoding="utf8",
              errors='ignore') as json_file:
        data = json.load(json_file)
        for district in data:
            try:
                District.objects.create(id=district['id'], name=district['name'],
                                        region_id=district['region_id'])
            except IntegrityError:
                district_obj = District.objects.get(id=district['id'])
                district_obj.name = district['name']
                district_obj.save()
    return District.objects.all()
