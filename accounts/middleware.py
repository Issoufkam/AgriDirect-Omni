import uuid
from datetime import datetime, timedelta
from .models import UserActivity

class TrackingMiddleware:
    """
    Middleware pour la collecte de données via cookies.
    Génère un tracking_id unique persistant pour chaque visiteur.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Vérifier si un cookie de tracking existe déjà
        tracking_id = request.COOKIES.get('agridirect_tracker')
        is_new = False
        
        if not tracking_id:
            tracking_id = str(uuid.uuid4())
            is_new = True

        # 2. Capturer l'activité (pour toutes les requêtes sauf les fichiers statiques/média pour éviter le bruit)
        if not request.path.startswith(('/static/', '/media/', '/favicon.ico')):
            UserActivity.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key if request.session.session_key else None,
                tracking_id=tracking_id,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                path=request.path,
                method=request.method
            )

        # 3. Récupérer la réponse
        response = self.get_response(request)

        # 4. Assurer que le cookie est défini sur la réponse si nouveau ou manquant
        if is_new or not request.COOKIES.get('agridirect_tracker'):
            # Expire dans 1 an
            expires = datetime.now() + timedelta(days=365)
            response.set_cookie(
                'agridirect_tracker', 
                tracking_id, 
                expires=expires,
                httponly=True, # Sécurité supplémentaire
                samesite='Lax'
            )
            
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
