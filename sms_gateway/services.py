"""
Services métier pour l'application SMS Gateway.

Contient le moteur de parsing SMS et l'intégration Africa's Talking.
"""

import logging
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from products.models import Product, Stock

from .models import SMSLog

logger = logging.getLogger("sms_gateway")
User = get_user_model()


# ==============================================================================
# DICTIONNAIRE DE PRODUITS (Mapping noms locaux → produit en base)
# ==============================================================================

PRODUCT_ALIASES = {
    # ── Vivriers ──
    "MAIS": "Maïs",
    "MAÏS": "Maïs",
    "RIZ": "Riz",
    "IGNAME": "Igname",
    "MANIOC": "Manioc",
    "BANANE": "Banane plantain",
    "PLANTAIN": "Banane plantain",
    "ATIEKE": "Attiéké",
    "ATTIEKE": "Attiéké",
    "ATTIÉKÉ": "Attiéké",
    "TOMATE": "Tomate",
    "OIGNON": "Oignon",
    "PIMENT": "Piment",
    "GOMBO": "Gombo",
    "AUBERGINE": "Aubergine",
    # ── Carnés ──
    "BOEUF": "Bœuf",
    "BŒUF": "Bœuf",
    "MOUTON": "Mouton",
    "CHEVRE": "Chèvre",
    "CHÈVRE": "Chèvre",
    "POULET": "Poulet",
    "PORC": "Porc",
    # ── Halieutiques ──
    "CARPE": "Carpe",
    "TILAPIA": "Tilapia",
    "THON": "Thon",
    "SARDINE": "Sardine",
    "CREVETTE": "Crevette",
    "CREVETTES": "Crevette",
    "CAPITAINE": "Capitaine",
    "MACHOIRON": "Machoiron",
    # ── Élevage ──
    "OEUF": "Œuf",
    "OEUFS": "Œuf",
    "ŒUF": "Œuf",
    "ŒUFS": "Œuf",
    "LAIT": "Lait",
}

UNIT_ALIASES = {
    "KG": "KG",
    "KILO": "KG",
    "KILOS": "KG",
    "KILOGRAMME": "KG",
    "KILOGRAMMES": "KG",
    "TETE": "TETE",
    "TÊTE": "TETE",
    "TÊTES": "TETE",
    "TETES": "TETE",
    "SAC": "SAC",
    "SACS": "SAC",
    "CASIER": "CASIER",
    "CASIERS": "CASIER",
    "TAS": "TAS",
}


@dataclass
class ParsedSMS:
    """Résultat du parsing d'un SMS."""

    action: str  # VENDRE, ACHETER, etc.
    product_name: str  # Nom du produit identifié
    quantity: Decimal  # Quantité
    unit: str  # Unité (KG, TETE, SAC, etc.)
    raw_text: str  # Texte original


class SMSParseError(Exception):
    """Erreur lors du parsing d'un SMS."""
    pass


def parse_sms(raw_text: str) -> ParsedSMS:
    """
    Analyse un SMS brut pour en extraire l'action, le produit,
    la quantité et l'unité.

    Formats supportés :
        "VENDRE <PRODUIT> <QUANTITE> <UNITE>"
        "VENDRE <QUANTITE> <UNITE> <PRODUIT>"
        "VENDRE <PRODUIT> <QUANTITE>"  (unité par défaut du produit)

    Exemples :
        "VENDRE MAIS 50 KG"       → Maïs, 50 KG
        "VENDRE BOEUF 2 TETE"     → Bœuf, 2 TETE
        "VENDRE CARPE 10 KG"      → Carpe, 10 KG
        "VENDRE 3 CASIER TOMATE"  → Tomate, 3 CASIER

    Args:
        raw_text: Texte brut du SMS.

    Returns:
        Instance ParsedSMS avec les données extraites.

    Raises:
        SMSParseError: Si le format est invalide ou le produit inconnu.
    """
    text = raw_text.strip().upper()
    text = re.sub(r"\s+", " ", text)  # Normaliser les espaces

    # Vérifier que le SMS commence par une action connue
    actions = ["VENDRE", "STOCK", "AJOUTER"]
    action = None
    for a in actions:
        if text.startswith(a):
            action = a
            text = text[len(a):].strip()
            break

    if not action:
        raise SMSParseError(
            "Format invalide. Commencez par VENDRE suivi du produit et de la quantité. "
            "Exemple: VENDRE MAIS 50 KG"
        )

    # Extraire les tokens
    tokens = text.split()
    if len(tokens) < 2:
        raise SMSParseError(
            "Format invalide. Indiquez au moins le produit et la quantité. "
            "Exemple: VENDRE MAIS 50 KG"
        )

    # Stratégie 1: "PRODUIT QUANTITE UNITE" (ex: "MAIS 50 KG")
    # Stratégie 2: "QUANTITE UNITE PRODUIT" (ex: "50 KG MAIS")
    # Stratégie 3: "PRODUIT QUANTITE" (ex: "MAIS 50")

    product_name = None
    quantity = None
    unit = None

    # Essayer de trouver le nombre (quantité)
    quantity_idx = None
    for i, token in enumerate(tokens):
        try:
            Decimal(token)
            quantity_idx = i
            break
        except InvalidOperation:
            continue

    if quantity_idx is None:
        raise SMSParseError(
            "Quantité non trouvée. Indiquez un nombre. "
            "Exemple: VENDRE MAIS 50 KG"
        )

    quantity = Decimal(tokens[quantity_idx])

    if quantity <= 0:
        raise SMSParseError("La quantité doit être supérieure à 0.")

    # Identifier l'unité (après la quantité)
    if quantity_idx + 1 < len(tokens) and tokens[quantity_idx + 1] in UNIT_ALIASES:
        unit = UNIT_ALIASES[tokens[quantity_idx + 1]]
        remaining_tokens = (
            tokens[:quantity_idx] + tokens[quantity_idx + 2 :]
        )
    else:
        remaining_tokens = tokens[:quantity_idx] + tokens[quantity_idx + 1 :]

    # Les tokens restants sont le nom du produit
    if not remaining_tokens:
        raise SMSParseError(
            "Produit non identifié. "
            "Exemple: VENDRE MAIS 50 KG"
        )

    product_token = " ".join(remaining_tokens)

    # Chercher le produit dans les alias
    if product_token in PRODUCT_ALIASES:
        product_name = PRODUCT_ALIASES[product_token]
    else:
        # Essayer token par token
        for token in remaining_tokens:
            if token in PRODUCT_ALIASES:
                product_name = PRODUCT_ALIASES[token]
                break

    if not product_name:
        raise SMSParseError(
            f"Produit '{product_token}' non reconnu. "
            "Produits acceptés: Maïs, Riz, Igname, Bœuf, Mouton, Carpe, etc."
        )

    # Si pas d'unité trouvée, utiliser l'unité par défaut du produit
    if unit is None:
        try:
            product_obj = Product.objects.get(name=product_name)
            unit = product_obj.unit
        except Product.DoesNotExist:
            unit = "KG"  # Fallback

    return ParsedSMS(
        action=action,
        product_name=product_name,
        quantity=quantity,
        unit=unit,
        raw_text=raw_text,
    )


@transaction.atomic
def process_stock_sms(
    phone_number: str,
    raw_text: str,
    latitude: float = None,
    longitude: float = None,
) -> dict:
    """
    Traite un SMS de mise à jour de stock.

    Étapes :
        1. Identifie l'utilisateur via son numéro de téléphone.
        2. Parse le SMS pour extraire produit, quantité, unité.
        3. Crée ou met à jour le stock du producteur.
        4. Enregistre le SMS dans le journal.
        5. Envoie un SMS de confirmation.

    Args:
        phone_number: Numéro de téléphone de l'expéditeur.
        raw_text: Texte brut du SMS.
        latitude: Latitude GPS du producteur (optionnel).
        longitude: Longitude GPS du producteur (optionnel).

    Returns:
        Dictionnaire avec le résultat du traitement.

    Raises:
        SMSParseError: Si le parsing échoue.
    """

    # ── 1. Identifier l'utilisateur ──
    try:
        user = User.objects.get(phone_number=phone_number)
    except User.DoesNotExist:
        # Créer un log d'erreur
        SMSLog.objects.create(
            direction=SMSLog.Direction.INBOUND,
            phone_number=phone_number,
            raw_text=raw_text,
            status=SMSLog.Status.ERROR,
            error_message="Utilisateur non trouvé.",
        )
        raise SMSParseError(
            "Numéro non enregistré. Inscrivez-vous d'abord sur AgriDirect."
        )

    if not user.is_producteur:
        SMSLog.objects.create(
            direction=SMSLog.Direction.INBOUND,
            phone_number=phone_number,
            raw_text=raw_text,
            status=SMSLog.Status.ERROR,
            error_message="L'utilisateur n'est pas un producteur.",
            user=user,
        )
        raise SMSParseError(
            "Seuls les producteurs peuvent déclarer des stocks par SMS."
        )

    # ── 2. Parser le SMS ──
    sms_log = SMSLog.objects.create(
        direction=SMSLog.Direction.INBOUND,
        phone_number=phone_number,
        raw_text=raw_text,
        status=SMSLog.Status.RECEIVED,
        user=user,
    )

    try:
        parsed = parse_sms(raw_text)
    except SMSParseError as e:
        sms_log.status = SMSLog.Status.ERROR
        sms_log.error_message = str(e)
        sms_log.save()
        raise

    sms_log.parsed_data = {
        "action": parsed.action,
        "product": parsed.product_name,
        "quantity": str(parsed.quantity),
        "unit": parsed.unit,
    }
    sms_log.status = SMSLog.Status.PARSED
    sms_log.save()

    # ── 3. Trouver le produit en base ──
    try:
        product = Product.objects.get(name=parsed.product_name, is_active=True)
    except Product.DoesNotExist:
        sms_log.status = SMSLog.Status.ERROR
        sms_log.error_message = f"Produit '{parsed.product_name}' non trouvé en base."
        sms_log.save()
        raise SMSParseError(
            f"Le produit '{parsed.product_name}' n'est pas encore référencé "
            "sur la plateforme."
        )

    # ── 4. Déterminer la localisation ──
    loc_lat = latitude
    loc_lng = longitude

    if loc_lat is None or loc_lng is None:
        if user.current_location_lat and user.current_location_lng:
            loc_lat = user.current_location_lat
            loc_lng = user.current_location_lng
        else:
            # Position par défaut : Abidjan
            loc_lat = 5.3600
            loc_lng = -3.9962
            logger.warning(
                "SMS de %s: pas de localisation → position par défaut (Abidjan).",
                phone_number,
            )

    # ── 5. Créer ou mettre à jour le stock ──
    stock, created = Stock.objects.update_or_create(
        producer=user,
        product=product,
        defaults={
            "quantity": parsed.quantity,
            "remaining_quantity": parsed.quantity,
            "location_lat": loc_lat,
            "location_lng": loc_lng,
            "needs_refrigeration": product.needs_refrigeration,
        },
    )

    if not created:
        # Si le stock existe, on ajoute la quantité
        stock.quantity += parsed.quantity
        stock.remaining_quantity += parsed.quantity
        stock.location_lat = loc_lat
        stock.location_lng = loc_lng
        stock.save()

    sms_log.status = SMSLog.Status.PROCESSED
    sms_log.save()

    # ── 6. Préparer la réponse SMS ──
    action_label = "créé" if created else "mis à jour"
    confirmation_text = (
        f"AgriDirect: Stock {action_label}! "
        f"{parsed.product_name}: {parsed.quantity} {parsed.unit} "
        f"à {product.national_price} FCFA/{parsed.unit}. "
        f"Stock total: {stock.remaining_quantity} {parsed.unit}."
    )

    # Simuler l'envoi du SMS de confirmation
    send_sms(phone_number, confirmation_text)

    # Journal du SMS sortant
    SMSLog.objects.create(
        direction=SMSLog.Direction.OUTBOUND,
        phone_number=phone_number,
        raw_text=confirmation_text,
        status=SMSLog.Status.SENT,
        user=user,
    )

    logger.info(
        "SMS traité: %s → Stock %s pour %s (%s %s %s).",
        phone_number,
        action_label,
        parsed.product_name,
        parsed.quantity,
        parsed.unit,
        product.national_price,
    )

    return {
        "success": True,
        "action": action_label,
        "product": parsed.product_name,
        "quantity": str(parsed.quantity),
        "unit": parsed.unit,
        "national_price": str(product.national_price),
        "remaining_stock": str(stock.remaining_quantity),
        "confirmation_sms": confirmation_text,
    }


def send_sms(phone_number: str, message: str) -> bool:
    """
    Envoie un SMS via Africa's Talking (simulation).

    En production, cette fonction intégrerait le SDK Africa's Talking.
    En développement, elle journalise simplement le message.

    Args:
        phone_number: Numéro du destinataire.
        message: Contenu du SMS.

    Returns:
        True si l'envoi est réussi.
    """
    at_username = settings.AT_USERNAME
    at_api_key = settings.AT_API_KEY

    if at_username == "sandbox" or not at_api_key:
        # Mode simulation
        logger.info(
            "[SMS SIMULÉ] → %s: %s",
            phone_number,
            message,
        )
        return True

    # ── Intégration Africa's Talking (production) ──
    # import africastalking
    # africastalking.initialize(at_username, at_api_key)
    # sms = africastalking.SMS
    # try:
    #     response = sms.send(message, [phone_number])
    #     logger.info("SMS envoyé à %s: %s", phone_number, response)
    #     return True
    # except Exception as e:
    #     logger.error("Erreur envoi SMS à %s: %s", phone_number, e)
    #     return False

    logger.warning("Africa's Talking non configuré. SMS non envoyé.")
    return False
