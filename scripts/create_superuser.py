import os
import sys

if __name__ == '__main__':
    # Configure Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vetsystem.settings')
    try:
        import django
        django.setup()
    except Exception as exc:
        print('Error setting up Django:', exc)
        sys.exit(1)

    from django.contrib.auth import get_user_model

    User = get_user_model()

    username = os.environ.get('SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('SUPERUSER_PASSWORD', 'admin')

    if not username or not password:
        print('Environment variables SUPERUSER_USERNAME and SUPERUSER_PASSWORD must be set')
        sys.exit(1)

    obj, created = User.objects.get_or_create(username=username, defaults={'email': email})
    if created:
        obj.set_password(password)
        obj.is_staff = True
        obj.is_superuser = True
        obj.save()
        print(f'Superuser "{username}" created')
    else:
        # Update password/email and ensure privileges
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
            print(f'Superuser "{username}" updated')
        else:
            print(f'Superuser "{username}" already exists and is up-to-date')
