import os
import django

# Django setup karo
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "babushonawear.settings")
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model

def setup():
    print("🔄 Running Database Migrations...")
    # 1. Jo error aa raha tha 'relation store_category does not exist', ye usko fix karega
    call_command("migrate")
    
    # 2. Superuser (Admin) Check & Create
    User = get_user_model()
    USERNAME = "admin"  # Apna Username
    EMAIL = "admin@gmail.com" # Apna Email
    PASSWORD = "admin"  # Apna Password (Change kar lena)

    if not User.objects.filter(username=USERNAME).exists():
        print("👑 Creating Superuser...")
        User.objects.create_superuser(USERNAME, EMAIL, PASSWORD)
        print("✅ Superuser 'admin' created successfully!")
    else:
        print("ℹ️ Superuser already exists.")

if __name__ == "__main__":
    setup()