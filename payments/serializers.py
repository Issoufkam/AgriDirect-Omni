from rest_framework import serializers

class PaymentInitializeSerializer(serializers.Serializer):
    """
    Serializer pour initialiser un paiement.
    """
    provider = serializers.ChoiceField(
        choices=["WAVE", "ORANGE_MONEY", "MTN_MOMO"],
        help_text="Fournisseur Mobile Money (ex: WAVE)."
    )
