from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_order_confirmation_email(order_id):
    from .models import Order
    order = Order.objects.select_related('user').get(id=order_id)
    
    send_mail(
        subject=f"Order Confirmation - Order #{order.id}",
        message=f"Thank you for your order! Your order #{order.id} has been placed and is now {order.get_status_display()}.",
        from_email=None,
        recipient_list=[order.user.email],
    )
