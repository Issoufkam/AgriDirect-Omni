import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Product, Stock
from django.contrib.auth import get_user_model

User = get_user_model()
print('--- Products ---')
for p in Product.objects.all():
    print(f'{p.id}: {p.name}')
    
print('\n--- Users ---')
for u in User.objects.all():
    print(f'{u.phone_number}: {u.get_full_name()} (ID: {u.id})')
    
print('\n--- Stocks ---')
for s in Stock.objects.all():
    print(f'Stock ID {s.id}: {s.quantity} {s.product.name} (Producer: {s.producer.phone_number})')
