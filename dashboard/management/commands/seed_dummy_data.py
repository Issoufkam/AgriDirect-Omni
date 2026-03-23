import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from phonenumber_field.phonenumber import PhoneNumber

from accounts.models import CustomUser
from products.models import Product, Stock
from orders.models import Order
from deliveries.models import Delivery

class Command(BaseCommand):
    help = "Génère des données de simulation (Utilisateurs, Stocks, Commandes, Livraisons) pour le Dashboard."

    def generate_phone(self):
        # Générer un faux numéro ivoirien aléatoire
        network = random.choice(["01", "05", "07"])
        return f"+225{network}{random.randint(10000000, 99999999)}"

    def handle(self, *args, **kwargs):
        self.stdout.write("Suppression des anciennes données de simulation...")
        
        # On pourrait supprimer l'existant, mais on va plutôt en ajouter
        # pour faire grossir le dashboard

        # 1. Création des Utilisateurs
        self.stdout.write("Création de 20 Utilisateurs (Clients, Producteurs, Livreurs)...")
        clients = []
        producers = []
        drivers = []

        # 10 Clients
        for i in range(10):
            user = CustomUser.objects.create_user(
                phone_number=self.generate_phone(),
                password="password123",
                first_name=f"Client",
                last_name=f"Demo {i}",
                role=CustomUser.Role.CLIENT,
                current_location_lat=5.3 + random.uniform(-0.05, 0.05), # Autour d'Abidjan
                current_location_lng=-4.0 + random.uniform(-0.05, 0.05)
            )
            clients.append(user)

        # 5 Producteurs
        for i in range(5):
            user = CustomUser.objects.create_user(
                phone_number=self.generate_phone(),
                password="password123",
                first_name=f"Producteur",
                last_name=f"Agricole {i}",
                role=CustomUser.Role.PRODUCTEUR,
                current_location_lat=6.8 + random.uniform(-0.5, 0.5), # Intérieur du pays
                current_location_lng=-5.2 + random.uniform(-0.5, 0.5)
            )
            producers.append(user)

        # 5 Livreurs
        for i in range(5):
            user = CustomUser.objects.create_user(
                phone_number=self.generate_phone(),
                password="password123",
                first_name=f"Livreur",
                last_name=f"Express {i}",
                role=CustomUser.Role.LIVREUR,
                is_active_driver=random.choice([True, True, False]), # Majorité actifs
                current_location_lat=5.3 + random.uniform(-0.1, 0.1),
                current_location_lng=-4.0 + random.uniform(-0.1, 0.1)
            )
            drivers.append(user)

        # Vérifier si des produits existent
        products = list(Product.objects.filter(is_active=True))
        if not products:
            self.stdout.write(self.style.ERROR("Aucun produit trouvé. Exécutez 'python manage.py seed_products' d'abord."))
            return

        # 2. Création de Stocks
        self.stdout.write("Création de Stocks...")
        stocks = []
        for producer in producers:
            # Chaque producteur a 2 à 4 produits
            producer_products = random.sample(products, random.randint(2, 4))
            for product in producer_products:
                qty = Decimal(random.randint(50, 500))
                stock, created = Stock.objects.get_or_create(
                    producer=producer,
                    product=product,
                    defaults={
                        'quantity': qty,
                        'remaining_quantity': qty,
                        'location_lat': producer.current_location_lat,
                        'location_lng': producer.current_location_lng
                    }
                )
                stocks.append(stock)

        # 3. Création des Commandes
        self.stdout.write("Création de 40 Commandes aléatoires...")
        orders = []
        status_weights = [Order.Status.PENDING] * 5 + [Order.Status.ASSIGNED] * 5 + [Order.Status.DELIVERED] * 25 + [Order.Status.CANCELLED] * 5
        
        for i in range(40):
            client = random.choice(clients)
            stock = random.choice(stocks)
            qty = Decimal(random.randint(1, 10))
            
            # Ajuster le stock (si on simule une réalité)
            if stock.remaining_quantity >= qty:
                stock.remaining_quantity -= qty
                stock.save()
            else:
                continue

            unit_price = stock.product.national_price
            total_prod = qty * unit_price
            delivery_fee = Decimal(random.randint(500, 3000))
            
            status = random.choice(status_weights)
            
            payment_status = Order.PaymentStatus.UNPAID
            if status == Order.Status.DELIVERED:
                payment_status = Order.PaymentStatus.RELEASED
            elif status in [Order.Status.ASSIGNED, Order.Status.PENDING]:
                payment_status = Order.PaymentStatus.ESCROWED # Simuler qu'ils ont payé via Mobile Money

            order = Order.objects.create(
                client=client,
                stock=stock,
                quantity=qty,
                unit_price=unit_price,
                total_product_amount=total_prod,
                delivery_fee=delivery_fee,
                total_amount=total_prod + delivery_fee,
                status=status,
                payment_status=payment_status,
                delivery_address="Quartier Résidentiel, Rue 12",
                client_location_lat=client.current_location_lat,
                client_location_lng=client.current_location_lng,
                transaction_id=f"WAVE-SIMULATION-{random.randint(1000, 9999)}",
                payment_provider="WAVE"
            )
            
            # Reculer la date de création pour enrichir les graphes historiques si nécessaire
            order.created_at = timezone.now() - timedelta(days=random.randint(0, 10))
            order.save(update_fields=['created_at'])
            
            orders.append(order)

        # 4. Création des Livraisons pour les commandes Assignées/Livrées
        self.stdout.write("Assignation des courses aux Livreurs...")
        for order in orders:
            if order.status in [Order.Status.ASSIGNED, Order.Status.DELIVERED, Order.Status.PICKED_UP]:
                driver = random.choice(drivers)
                del_status = Delivery.Status.DELIVERED if order.status == Order.Status.DELIVERED else Delivery.Status.EN_ROUTE_DELIVERY
                
                delivery = Delivery.objects.create(
                    order=order,
                    driver=driver,
                    status=del_status,
                    delivery_fee=order.delivery_fee,
                    otp_code=f"{random.randint(100000, 999999)}"
                )
                
                if del_status == Delivery.Status.DELIVERED:
                    delivery.pickup_time = order.created_at + timedelta(hours=1)
                    delivery.delivery_time = order.created_at + timedelta(hours=3)
                    delivery.save(update_fields=['pickup_time', 'delivery_time'])

        self.stdout.write(self.style.SUCCESS('Seeding terminé avec succès! Le Dashboard va exploser de données !'))
