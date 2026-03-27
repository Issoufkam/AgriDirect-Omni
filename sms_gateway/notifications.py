import logging
from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)
from requests.exceptions import ConnectionError, HTTPError

logger = logging.getLogger("sms_gateway")

def send_push_notification(token: str, message: str, extra_data: dict = None):
    """
    Envoie une notification push via Expo.
    """
    if not token:
        return

    try:
        response = PushClient().publish(
            PushMessage(to=token, body=message, data=extra_data)
        )
    except PushServerError as exc:
        # Encountered some issues with the Expo push service itself.
        logger.error("Push Server Error: %s", exc)
        return False
    except (ConnectionError, HTTPError) as exc:
        # Encountered some transient network error.
        logger.error("Network error during push notification: %s", exc)
        return False

    try:
        # We got a response back, but we don't know if it's a success yet.
        # This will raise an exception if there is an error.
        response.validate_response()
    except DeviceNotRegisteredError:
        # Mark the push token as inactive
        from accounts.models import CustomUser
        CustomUser.objects.filter(expo_push_token=token).update(expo_push_token=None)
        logger.warning("Device not registered, token removed: %s", token)
    except PushTicketError as exc:
        # Encountered some other per-notification error.
        logger.error("Push Ticket Error: %s", exc)
        return False

    return True
