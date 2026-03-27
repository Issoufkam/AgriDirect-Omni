from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.db.models import Sum, Count, Q
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from datetime import timedelta

from accounts.models import CustomUser, UserActivity
from products.models import Stock, Product
from orders.models import Order
from deliveries.models import Delivery
from sms_gateway.models import SMSLog
from sms_gateway.services import process_stock_sms

class CentralDashboardStatsView(generics.GenericAPIView):
    """
    Retourne les statistiques globales de la plateforme AgriDirect-CIV.
    Accessible uniquement aux administrateurs ou à un rôle spécifique de Superviseur.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Statistiques du Dashboard Central",
        description="Récupère les KPIS globaux (utilisateurs, produits, commandes, livraisons) pour alimenter le tableau de bord de l'application.",
        responses={
            200: OpenApiResponse(description="Statistiques récupérées avec succès")
        }
    )
    def get(self, request, *args, **kwargs):
        # 1. KPIs Utilisateurs
        users_stats = CustomUser.objects.aggregate(
            total_clients=Count('id', filter=Q(role=CustomUser.Role.CLIENT)),
            total_producers=Count('id', filter=Q(role=CustomUser.Role.PRODUCTEUR)),
            total_drivers=Count('id', filter=Q(role=CustomUser.Role.LIVREUR)),
            active_drivers=Count('id', filter=Q(role=CustomUser.Role.LIVREUR, is_active_driver=True))
        )

        # 2. KPIs Produits & Stocks
        stock_stats = Stock.objects.filter(remaining_quantity__gt=0).aggregate(
            total_available_stocks=Count('id'),
            total_quantity=Sum('remaining_quantity')
        )
        total_products_referenced = Product.objects.filter(is_active=True).count()

        # 3. KPIs Commandes (Volume Financier et États)
        orders_stats = Order.objects.aggregate(
            total_orders=Count('id'),
            pending_orders=Count('id', filter=Q(status=Order.Status.PENDING)),
            delivered_orders=Count('id', filter=Q(status=Order.Status.DELIVERED)),
            cancelled_orders=Count('id', filter=Q(status=Order.Status.CANCELLED)),
            # Volume total des commandes livrées (en FCFA)
            total_revenue_fcfa=Sum('total_amount', filter=Q(status=Order.Status.DELIVERED))
        )

        # 4. KPIs Livraisons (Logistique)
        deliveries_stats = Delivery.objects.aggregate(
            total_deliveries=Count('id'),
            en_route=Count('id', filter=Q(status__in=[Delivery.Status.EN_ROUTE_PICKUP, Delivery.Status.EN_ROUTE_DELIVERY])),
            completed=Count('id', filter=Q(status=Delivery.Status.DELIVERED))
        )

        data = {
            "users": users_stats,
            "catalog": {
                "active_products": total_products_referenced,
                "available_stocks": stock_stats['total_available_stocks'] or 0,
                "total_volume_available": stock_stats['total_quantity'] or 0
            },
            "orders": {
                "total": orders_stats['total_orders'] or 0,
                "pending": orders_stats['pending_orders'] or 0,
                "delivered": orders_stats['delivered_orders'] or 0,
                "cancelled": orders_stats['cancelled_orders'] or 0,
                "total_revenue_fcfa": orders_stats['total_revenue_fcfa'] or 0
            },
            "logistics": {
                "total_deliveries": deliveries_stats['total_deliveries'] or 0,
                "en_route": deliveries_stats['en_route'] or 0,
                "completed": deliveries_stats['completed'] or 0,
                "active_drivers_on_map": users_stats['active_drivers'] or 0
            }
        }

        return Response(data, status=status.HTTP_200_OK)


class MapDataView(generics.GenericAPIView):
    """
    Retourne les données GPS pour la cartographie du dashboard.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Données Cartographiques",
        description="Retourne les localisations des livreurs, producteurs et livraisons en cours.",
    )
    def get(self, request, *args, **kwargs):
        # 1. Livreurs actifs
        drivers = CustomUser.objects.filter(
            role=CustomUser.Role.LIVREUR,
            is_active_driver=True,
            current_location_lat__isnull=False
        ).values('id', 'first_name', 'last_name', 'current_location_lat', 'current_location_lng', 'has_refrigeration')

        # 2. Producteurs avec stock
        producers = Stock.objects.filter(remaining_quantity__gt=0).select_related('producer').values(
            'id', 'producer__first_name', 'producer__last_name', 'location_lat', 'location_lng', 'product__name'
        )

        # 3. Livraisons en cours (Trajets)
        active_deliveries = Delivery.objects.filter(
            status__in=[Delivery.Status.EN_ROUTE_PICKUP, Delivery.Status.PICKED_UP, Delivery.Status.EN_ROUTE_DELIVERY]
        ).select_related('order', 'order__client', 'driver').values(
            'id', 'status',
            'order__client_location_lat', 'order__client_location_lng',
            'order__stock__location_lat', 'order__stock__location_lng',
            'driver__current_location_lat', 'driver__current_location_lng'
        )

        return Response({
            "drivers": list(drivers),
            "producers": list(producers),
            "deliveries": list(active_deliveries)
        }, status=status.HTTP_200_OK)


class RecentTransactionsView(generics.GenericAPIView):
    """
    Retourne la liste des transactions financières récentes (Paiements, Séquestres, Versements).
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Transactions Financières Récentes",
        description="Liste des flux d'argent sur la plateforme.",
    )
    def get(self, request, *args, **kwargs):
        # Récupérer les 15 dernières commandes ayant eu un flux financier
        transactions = Order.objects.exclude(payment_status=Order.PaymentStatus.UNPAID).order_by('-updated_at')[:15]
        
        data = []
        for t in transactions:
            data.append({
                "id": t.id,
                "client": t.client.get_full_name(),
                "producer": t.producer.get_full_name(),
                "amount": t.total_amount,
                "status": t.payment_status,
                "status_display": t.get_payment_status_display(),
                "provider": t.payment_provider,
                "date": t.updated_at.strftime("%d/%m/%Y %H:%M")
            })
            
        return Response(data, status=status.HTTP_200_OK)


class UserListView(generics.GenericAPIView):
    """
    Retourne la liste complète des utilisateurs filtrée par rôle si nécessaire.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Liste des Utilisateurs",
        description="Récupère la liste des clients, producteurs et livreurs.",
    )
    def get(self, request, *args, **kwargs):
        role_filter = request.query_params.get('role', None)
        
        users = CustomUser.objects.all()
        if role_filter:
            users = users.filter(role=role_filter)
            
        users = users.order_by('-date_joined')[:50] # Les 50 derniers
        
        data = []
        for u in users:
            data.append({
                "id": u.id,
                "name": u.get_full_name() or u.phone_number,
                "phone": str(u.phone_number),
                "role": u.role,
                "role_display": u.get_role_display(),
                "is_active": u.is_active,
                "date_joined": u.date_joined.strftime("%d/%m/%Y"),
                "is_active_driver": getattr(u, 'is_active_driver', False)
            })
            
        return Response(data, status=status.HTTP_200_OK)


class AnalyticsDataView(generics.GenericAPIView):
    """
    Fournit des analytiques basées sur le tracking (Pages populaires, Appareils, etc.).
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    @extend_schema(
        summary="Analytique d'activité",
        description="Données d'utilisation issues des cookies de tracking.",
    )
    def get(self, request, *args, **kwargs):
        # 1. Top 5 Pages les plus vues
        top_paths = UserActivity.objects.values('path').annotate(
            visits=Count('id')
        ).order_by('-visits')[:5]

        # 2. Breakdown des User Agents (Simpliste: Mobile vs Desktop)
        # On va compter si 'Mobi' est dans la chaîne du user_agent
        mobile_count = UserActivity.objects.filter(user_agent__icontains='Mobi').count()
        total_count = UserActivity.objects.count()
        desktop_count = max(0, total_count - mobile_count)

        # 3. Visites par jour (7 derniers jours)
        seven_days_ago = timezone.now() - timedelta(days=7)
        # SQLite compatibility for date parsing in extra
        visits_over_time = UserActivity.objects.filter(timestamp__gte=seven_days_ago).extra(
            select={'day': "date(timestamp)"}
        ).values('day').annotate(count=Count('id')).order_by('day')

        # 4. Logs SMS Récents
        sms_logs = SMSLog.objects.all().order_by('-created_at')[:10]
        sms_data = []
        for log in sms_logs:
            sms_data.append({
                "direction": log.direction,
                "phone": str(log.phone_number),
                "text": log.raw_text,
                "status": log.status,
                "time": log.created_at.strftime("%H:%M:%S")
            })

        return Response({
            "top_paths": list(top_paths),
            "devices": {
                "mobile": mobile_count,
                "desktop": desktop_count
            },
            "timeline": list(visits_over_time),
            "sms_logs": sms_data
        }, status=status.HTTP_200_OK)


class SMSInboundSimulatorView(generics.GenericAPIView):
    """
    Simule la réception d'un SMS entrant d'un producteur.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, *args, **kwargs):
        # On choisit un producteur aléatoire du seeder
        producer = CustomUser.objects.filter(role=CustomUser.Role.PRODUCTEUR).first()
        if not producer:
            return Response({"error": "Aucun producteur en base."}, status=400)
            
        text = request.data.get('text', 'VENDRE IGNAME 25 KG')
        
        try:
            result = process_stock_sms(str(producer.phone_number), text)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class ProducerDashboardStatsView(generics.GenericAPIView):
    """
    Retourne les statistiques spécifiques à un PRODUCTEUR.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not request.user.role == CustomUser.Role.PRODUCTEUR:
            return Response({"detail": "Accessible uniquement aux producteurs."}, status=403)
        
        user = request.user
        
        # 1. KPIs Stocks
        stocks = Stock.objects.filter(producer=user)
        total_stocks = stocks.count()
        active_stocks = stocks.filter(remaining_quantity__gt=0).count()
        sold_out_stocks = stocks.filter(remaining_quantity=0).count()

        # 2. KPIs Commandes (liées à ses stocks)
        orders = Order.objects.filter(stock__producer=user)
        total_orders = orders.count()
        delivered_orders = orders.filter(status=Order.Status.DELIVERED).count()
        pending_orders = orders.filter(status__in=[Order.Status.PENDING, Order.Status.ASSIGNED]).count()

        # 3. KPIs Financiers
        total_revenue = orders.filter(status=Order.Status.DELIVERED).aggregate(Sum('total_product_amount'))['total_product_amount__sum'] or 0
        
        # 4. Évolution (Simulée pour le frontend: 30 derniers jours)
        # On pourrait faire un vrai count par date ici
        
        data = {
            "inventory": {
                "total": total_stocks,
                "active": active_stocks,
                "sold_out": sold_out_stocks
            },
            "orders": {
                "total": total_orders,
                "delivered": delivered_orders,
                "pending": pending_orders
            },
            "finance": {
                "total_revenue": total_revenue,
                "currency": "FCFA"
            },
            "performance": {
                "rating": user.average_rating,
                "trust_score": 95 # Simulation
            }
        }
        
        return Response(data, status=status.HTTP_200_OK)


class DashboardUIView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Vue pour afficher l'interface graphique du tableau de bord.
    Réservée aux administrateurs (Staff).
    """
    template_name = "dashboard/index.html"
    login_url = "/admin/login/" # Redirige vers le login admin si non connecté

    def test_func(self):
        # Seul le staff (Admin) peut accéder au Dashboard Central
        return self.request.user.is_staff

