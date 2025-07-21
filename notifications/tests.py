import pytest
from users.models import CustomUser as User  # ✅ Use your actual user model
from notifications.models import Notification

@pytest.mark.django_db
def test_notification_creation():
    user = User.objects.create_user(username="user1", email="n@notify.com", password="pass")

    if hasattr(user, 'user_type'):
        user.user_type = "client"
        user.save()

    notification = Notification.objects.create(
        user=user,
        message="New message received",
        notification_type="message"
    )

    assert notification.pk is not None
    assert notification.user == user
