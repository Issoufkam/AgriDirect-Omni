from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from django.db import IntegrityError

from .models import Review
from orders.models import Order

class ReviewSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'order', 'target_type', 'rating', 'comment', 'created_at', 'client_name']
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
        
        try:
            order = Order.objects.get(pk=serializer.validated_data['order'].id, client=request.user)
        except Order.DoesNotExist:
             return Response({"detail": "Commande introuvable ou vous n'êtes pas l'auteur."}, status=status.HTTP_404_NOT_FOUND)
        
        # Vérifier que la commande est livrée ou payée
        if order.status != Order.Status.DELIVERED:
             return Response({"detail": "La commande doit être livrée pour être notée."}, status=status.HTTP_400_BAD_REQUEST)

        # Sauvegarde with IntegrityError protection
        try:
            serializer.save(client=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({"detail": "Vous avez déjà soumis un avis pour cette cible sur cette commande."}, status=status.HTTP_400_BAD_REQUEST)


class ReviewListView(generics.ListAPIView):
    """
    GET /api/reviews/
    Liste les avis pour un producteur ou un livreur.
    Query params: user_id (int), target_type (PRODUIT/LIVREUR)
    """
    serializer_class = ReviewSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        target_type = self.request.query_params.get('target_type')
        
        queryset = Review.objects.all()
        if user_id:
            if target_type == 'LIVREUR':
                queryset = queryset.filter(order__delivery__driver_id=user_id, target_type='LIVREUR')
            else:
                queryset = queryset.filter(order__stock__producer_id=user_id, target_type='PRODUIT')
        
        return queryset
