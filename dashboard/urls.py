from django.urls import path
from .views import (
    CentralDashboardStatsView, 
    ProducerDashboardStatsView,
    DashboardUIView, 
    MapDataView, 
    RecentTransactionsView, 
    UserListView,
    AnalyticsDataView,
    SMSInboundSimulatorView
)

app_name = "dashboard"

urlpatterns = [
    path("dashboard/", DashboardUIView.as_view(), name="dashboard_ui"),
    path("api/dashboard/stats/", CentralDashboardStatsView.as_view(), name="dashboard_stats"),
    path("api/producer/dashboard/stats/", ProducerDashboardStatsView.as_view(), name="producer_dashboard_stats"),
    path("api/dashboard/map/", MapDataView.as_view(), name="dashboard_map"),
    path("api/dashboard/transactions/", RecentTransactionsView.as_view(), name="dashboard_transactions"),
    path("api/dashboard/users/", UserListView.as_view(), name="dashboard_users"),
    path("api/dashboard/analytics/", AnalyticsDataView.as_view(), name="dashboard_analytics"),
    path("api/dashboard/simulate-sms/", SMSInboundSimulatorView.as_view(), name="dashboard_simulate_sms"),
]
