"""
Commande de gestion Django pour peupler la base de données
avec les produits référencés et leurs prix nationaux.

Usage:
    python manage.py seed_products
"""

from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    """Peuple la base de données avec les produits agricoles ivoiriens."""

    help = "Crée les produits référencés avec prix nationaux pour AgriDirect-CIV."

    PRODUCTS = [
        # ── VIVRIERS ──
        {"name": "Maïs", "category": "VIVRIER", "unit": "KG", "national_price": 350, "needs_refrigeration": False},
        {"name": "Riz", "category": "VIVRIER", "unit": "KG", "national_price": 450, "needs_refrigeration": False},
        {"name": "Igname", "category": "VIVRIER", "unit": "KG", "national_price": 400, "needs_refrigeration": False},
        {"name": "Manioc", "category": "VIVRIER", "unit": "KG", "national_price": 200, "needs_refrigeration": False},
        {"name": "Banane plantain", "category": "VIVRIER", "unit": "TAS", "national_price": 1000, "needs_refrigeration": False},
        {"name": "Attiéké", "category": "VIVRIER", "unit": "KG", "national_price": 300, "needs_refrigeration": False},
        {"name": "Tomate", "category": "VIVRIER", "unit": "CASIER", "national_price": 15000, "needs_refrigeration": True},
        {"name": "Oignon", "category": "VIVRIER", "unit": "SAC", "national_price": 25000, "needs_refrigeration": False},
        {"name": "Piment", "category": "VIVRIER", "unit": "TAS", "national_price": 500, "needs_refrigeration": False},
        {"name": "Gombo", "category": "VIVRIER", "unit": "TAS", "national_price": 500, "needs_refrigeration": True},
        {"name": "Aubergine", "category": "VIVRIER", "unit": "TAS", "national_price": 500, "needs_refrigeration": True},
        # ── CARNÉS ──
        {"name": "Bœuf", "category": "CARNE", "unit": "KG", "national_price": 3500, "needs_refrigeration": True},
        {"name": "Mouton", "category": "CARNE", "unit": "KG", "national_price": 4000, "needs_refrigeration": True},
        {"name": "Chèvre", "category": "CARNE", "unit": "KG", "national_price": 3800, "needs_refrigeration": True},
        {"name": "Poulet", "category": "CARNE", "unit": "TETE", "national_price": 3000, "needs_refrigeration": True},
        {"name": "Porc", "category": "CARNE", "unit": "KG", "national_price": 2500, "needs_refrigeration": True},
        # ── HALIEUTIQUES ──
        {"name": "Carpe", "category": "HALIEUTIQUE", "unit": "KG", "national_price": 2000, "needs_refrigeration": True},
        {"name": "Tilapia", "category": "HALIEUTIQUE", "unit": "KG", "national_price": 1800, "needs_refrigeration": True},
        {"name": "Thon", "category": "HALIEUTIQUE", "unit": "KG", "national_price": 3000, "needs_refrigeration": True},
        {"name": "Sardine", "category": "HALIEUTIQUE", "unit": "CASIER", "national_price": 20000, "needs_refrigeration": True},
        {"name": "Crevette", "category": "HALIEUTIQUE", "unit": "KG", "national_price": 5000, "needs_refrigeration": True},
        {"name": "Capitaine", "category": "HALIEUTIQUE", "unit": "KG", "national_price": 4000, "needs_refrigeration": True},
        {"name": "Machoiron", "category": "HALIEUTIQUE", "unit": "KG", "national_price": 2500, "needs_refrigeration": True},
        # ── ÉLEVAGE ──
        {"name": "Œuf", "category": "ELEVAGE", "unit": "CASIER", "national_price": 3500, "needs_refrigeration": True},
        {"name": "Lait", "category": "ELEVAGE", "unit": "KG", "national_price": 800, "needs_refrigeration": True},
    ]

    def handle(self, *args, **options):
        """Exécute la commande de peuplement."""
        created_count = 0
        updated_count = 0

        for product_data in self.PRODUCTS:
            product, created = Product.objects.update_or_create(
                name=product_data["name"],
                defaults={
                    "category": product_data["category"],
                    "unit": product_data["unit"],
                    "national_price": product_data["national_price"],
                    "needs_refrigeration": product_data["needs_refrigeration"],
                    "is_active": True,
                },
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Créé: {product.name} — {product.national_price} FCFA/{product.get_unit_display()}"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    f"  ~ Mis à jour: {product.name} — {product.national_price} FCFA/{product.get_unit_display()}"
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé: {created_count} produits créés, {updated_count} mis à jour."
            )
        )
