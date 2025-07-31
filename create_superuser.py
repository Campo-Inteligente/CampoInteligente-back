import os
import django
from django.contrib.auth.models import User

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "campointeligente.settings")
django.setup()

username = "admin"
password = "admin123"
email = "admin@admin.com"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("✅ Superusuário criado com sucesso!")
else:
    print("⚠️ O usuário já existe, nada foi alterado.")
