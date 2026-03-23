from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers

from .models import Review
from orders.models import Order

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'order', 'target_type', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']

class ReviewCreateView(APIView):
    """
    POST /api/reviews/
    Soumet un avis après livraison.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_client:
            return Response({"detail": "Seuls les clients peuvent noter."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order = Order.objects.get(pk=serializer.validated_data['order'].id)
        
        # Vérifier que la commande est livrée ou payée
        if order.status != Order.Status.DELIVERED:
             return Response({"detail": "La commande doit être livrée pour être notée."}, status=status.HTTP_400_BAD_REQUEST)

        # Sauvegarde
        serializer.save(client=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
