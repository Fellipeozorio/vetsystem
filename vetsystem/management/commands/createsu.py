import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create or update a superuser from environment variables: SUPERUSER_USERNAME, SUPERUSER_EMAIL, SUPERUSER_PASSWORD'

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        username = os.environ.get('SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('SUPERUSER_PASSWORD', 'admin')

        if not username or not password:
            self.stdout.write(self.style.ERROR('SUPERUSER_USERNAME and SUPERUSER_PASSWORD must be set'))
            return

        obj, created = User.objects.get_or_create(username=username, defaults={'email': email})
        if created:
            obj.set_password(password)
            obj.is_staff = True
            obj.is_superuser = True
            obj.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created'))
        else:
            changed = False
            if not obj.check_password(password):
                obj.set_password(password)
                changed = True
            if obj.email != email:
                obj.email = email
                changed = True
            if not obj.is_staff or not obj.is_superuser:
                obj.is_staff = True
                obj.is_superuser = True
                changed = True
            if changed:
                obj.save()
                self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" updated'))
            else:
                self.stdout.write(self.style.NOTICE(f'Superuser "{username}" already exists and is up-to-date'))
