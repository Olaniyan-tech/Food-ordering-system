from celery import shared_task
from food.selectors import get_order_by_id_for_email
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from food.models import Order
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

STATUS_EMAIL_MESSAGES = {
    "CONFIRMED" : {
        "subject": "Your order has been confirmed ✅",
        "message": "Your order has been confirmed and will soon start preparing.",
    },

    "PREPARING" : {
        "subject": "Your order is being prepared 🍳",
        "message": "Great news! The kitchen has started preparing your order. Sit tight!",
    },

    "READY": {
        "subject": "Your order is ready 🎉",
        "message": "Your order is ready and waiting for pickup by your delivery driver.",
    },

    "OUT FOR DELIVERY": {
        "subject": "Your order is on the way 🛵",
        "message": "The rider has picked up your order and is heading your way.",
    },

    "DELIVERED": {
        "subject": "Order delivered - enjoy your meal 🍽",
        "message": "Your order has been delivered. We hope you enjoyed it! Don't forget to leave a review.",
    },

    "CANCELLED": {
        "subject": "Your order has been cancelled ❌",
        "message": "Your order has been cancelled. If you have any questions, please contact us.",
    }

}


@shared_task(bind=True, max_retries=3)
def send_order_status_email(self, order_id, new_status):
    try:
        order = get_order_by_id_for_email(order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found, skipping email")
        return

    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )
        email_data = STATUS_EMAIL_MESSAGES.get(new_status)
        if not email_data:
            return
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": order.user.email, "name": order.user.username}],
            sender={"email": "alliolaniyan1@gmail.com", "name": "OlaTech Food"},
            subject=email_data["subject"],
            html_content=f"""
                <h2>Hi {order.user.username},</h2>
                <p>{email_data['message']}</p>
                <p>Order Total: ₦{order.total}</p>
                <p>Thank you for choosing OlaTech Food!</p>
            """
        )

        api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Status email sent to {order.user.email} for order {order.id} → {new_status}")

    except ApiException as exc:
        logger.error(f"Failed to send status email for order {order.id}: {exc} ")
        raise self.retry(exc=exc, countdown=60)
    

@shared_task(bind=True, max_retries=3)
def send_payment_email(self, order_id, payment_status):
    try:
        order = get_order_by_id_for_email(order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found, skipping email")
        return
    
    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = settings.BREVO_API_KEY

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        if payment_status == "PAID":
            subject = "Payment successful ✅"
            html_content = f"""
                <h2>Hi {order.user.username},</h2>
                <p>Your payment of ₦{order.total} has been received successfully.</p>
                <p>Payment Reference: <strong>{order.payment_reference}</strong></p>
                <p>Thank you for choosing OlaTech Food!</p>
            """

        else:
            subject = "Payment failed ❌"
            html_content = f"""
                <h2>Hi {order.user.username},</h2>
                <p>Unfortunately your payment for Order {order.payment_reference} failed.</p>
                <p>Please try again or contact support.</p>
                <p>OlaTech Food</p>
            """
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(            
            to=[{"email": order.user.email, "name": order.user.username}],
            sender={"email": "alliolaniyan1@gmail.com", "name": "OlaTech Food"},
            subject=subject,
            html_content=html_content
        )

        api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Payment email sent to {order.user.email} — {payment_status}")
    
    except ApiException as exc:
        logger.error(f"Failed to send payment email for order {order_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


