from celery import shared_task
from .models import UserActivity, CustomUser

@shared_task
def record_user_activity(user_id, tracking_id, session_key, ip_address, user_agent, path, method):
    """
    Enregistre l'activité de l'utilisateur de manière asynchrone via Celery.
    """
    user = None
    if user_id:
        try:
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            pass
            
    UserActivity.objects.create(
        user=user,
        tracking_id=tracking_id,
        session_key=session_key,
        ip_address=ip_address,
        user_agent=user_agent,
        path=path,
        method=method
    )
