import os
import django
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_dev")
django.setup()

from accounts.models import CustomUser
from products.models import Product, Stock
from orders.models import Order
from deliveries.services import assign_delivery

def create_mock_order():
    # 1. Trouver un producteur
    producers = CustomUser.objects.filter(role=CustomUser.Role.PRODUCTEUR)
    if not producers.exists():
        print("Erreur: Aucun producteur trouvé en base.")
        return
    producer = producers.first()

    # 2. Vérifier s'il a au moins un stock, sinon on en crée un
    stock = Stock.objects.filter(producer=producer).first()
    if not stock:
        # Trouver ou créer un produit
        product, _ = Product.objects.get_or_create(
            name="Tomates de test",
            defaults={"category": "VIVRIER", "national_price": 500}
        )
        stock = Stock.objects.create(
            producer=producer,
            product=product,
            quantity=100.0,
            location_lat=5.345,
            location_lng=-4.024
        )

    # 3. Trouver un client
    client, _ = CustomUser.objects.get_or_create(
        phone_number="+2250102030405",
        defaults={"role": CustomUser.Role.CLIENT, "first_name": "Client", "last_name": "Test"}
    )
    if client.role != CustomUser.Role.CLIENT:
        client.role = CustomUser.Role.CLIENT
        client.save()

    # 4. Trouver ou créer un livreur
    driver, _ = CustomUser.objects.get_or_create(
        phone_number="+2250505050505",
        defaults={
            "role": CustomUser.Role.LIVREUR, 
            "first_name": "Jean", 
            "last_name": "Livreur",
            "is_active_driver": True,
            "current_location_lat": 5.350,
            "current_location_lng": -4.030
        }
    )
    if driver.role != CustomUser.Role.LIVREUR:
        driver.role = CustomUser.Role.LIVREUR
        driver.save()

    # 5. Créer une commande PENDING
    order = Order.objects.create(
        client=client,
        stock=stock,
        quantity=10,
        unit_price=stock.product.national_price,
        delivery_address="Plateau, Abidjan",
        client_location_lat=5.355,
        client_location_lng=-4.015,
        status=Order.Status.PENDING,
        total_product_amount=stock.product.national_price * 10,
        delivery_fee=1500,
        total_amount=(stock.product.national_price * 10) + 1500
    )

    # 6. Assigner le livreur à la commande (Passe la commande en ASSIGNED et génère l'OTP)
    delivery = assign_delivery(order, driver)

    print(f"✅ Succès ! Commande de test #{order.id} générée avec le statut: {order.status}")
    print(f"👉 Le Livreur {driver.get_full_name()} a été assigné (Livraison #{delivery.id})")
    print(f"🔒 Le fameux code OTP généré est : {delivery.otp_code}")

if __name__ == "__main__":
    create_mock_order()
