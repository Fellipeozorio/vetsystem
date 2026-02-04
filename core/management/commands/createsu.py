from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    help = 'Cria superusuário automaticamente se não existir'

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.getenv('DJANGO_SUPERUSER_USERNAME')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write('Variáveis de superusuário não definidas')
            return

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write('Superusuário criado com sucesso')
        else:
            self.stdout.write('Superusuário já existe')
