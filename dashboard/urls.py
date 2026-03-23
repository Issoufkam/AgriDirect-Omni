from django.urls import path
from .views import (
    CentralDashboardStatsView, 
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
    path("dashboard/stats/", CentralDashboardStatsView.as_view(), name="dashboard_stats"),
    path("dashboard/map/", MapDataView.as_view(), name="dashboard_map"),
    path("dashboard/transactions/", RecentTransactionsView.as_view(), name="dashboard_transactions"),
    path("dashboard/users/", UserListView.as_view(), name="dashboard_users"),
    path("dashboard/analytics/", AnalyticsDataView.as_view(), name="dashboard_analytics"),
    path("dashboard/simulate-sms/", SMSInboundSimulatorView.as_view(), name="dashboard_simulate_sms"),
]
