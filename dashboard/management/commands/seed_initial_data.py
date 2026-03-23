from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = "Initialise les produits officiels de la plateforme."

    def handle(self, *args, **kwargs):
        products_data = [
            {"name": "Riz Local (50kg)", "category": Product.Category.VIVRIER, "unit": Product.Unit.SAC, "national_price": 25000},
            {"name": "Maïs Jaune (1kg)", "category": Product.Category.VIVRIER, "unit": Product.Unit.KG, "national_price": 450},
            {"name": "Bœuf (1kg)", "category": Product.Category.CARNE, "unit": Product.Unit.KG, "national_price": 3500, "needs_refrigeration": True},
            {"name": "Carpe (1kg)", "category": Product.Category.HALIEUTIQUE, "unit": Product.Unit.KG, "national_price": 2800, "needs_refrigeration": True},
            {"name": "Ananas (1kg)", "category": Product.Category.VIVRIER, "unit": Product.Unit.KG, "national_price": 600},
            {"name": "Manioc (Tas)", "category": Product.Category.VIVRIER, "unit": Product.Unit.TAS, "national_price": 1000},
        ]

        for p_data in products_data:
            product, created = Product.objects.get_or_create(
                name=p_data["name"],
                defaults=p_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Produit créé: {product.name}"))
            else:
                self.stdout.write(f"Le produit existe déjà: {product.name}")
