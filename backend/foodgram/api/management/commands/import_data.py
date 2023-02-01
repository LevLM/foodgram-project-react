import os
from csv import reader

from django.conf import settings
from django.core.management import BaseCommand
from recipes.models import Ingredient

DATA_PATH = os.path.join(settings.BASE_DIR, 'data')
INGREDIENTS_DATA = os.path.join(DATA_PATH, 'ingredients.csv')


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        with open(INGREDIENTS_DATA, 'r', encoding='UTF-8') as ingredients:
            for row in reader(ingredients):
                if len(row) == 2:
                    Ingredient.objects.get_or_create(
                        name=row[0],
                        measurement_unit=row[1],
                    )
