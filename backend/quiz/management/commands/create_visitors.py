from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from faker import Faker


fake = Faker()


class Command(BaseCommand):
    help = 'Наполнить базу данных, базовыми типами вопросов.'

    def handle(self, *args, **kwargs):
        profile = fake.simple_profile()
        user = get_user_model().objects.create(username=profile['username'], is_superuser=0)
        user.set_password(profile['username'])
        self.stdout.write(f"username: {user}\nid: {user.id}")

