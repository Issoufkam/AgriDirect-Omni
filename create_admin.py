import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_dev')
django.setup()

from accounts.models import CustomUser

phone_number = "0000000000"
password = "admin"

if not CustomUser.objects.filter(phone_number=phone_number).exists():
    user = CustomUser.objects.create_superuser(phone_number, password=password)
    print(f"Superutilisateur créé avec succès : {phone_number} / {password}")
else:
    print(f"Le superutilisateur {phone_number} existe déjà.")
