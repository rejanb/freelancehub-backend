
import pytest
from django.contrib.auth import get_user_model
from chats.models import Chat

User = get_user_model()

@pytest.mark.django_db
def test_chat_message_creation():
    sender = User.objects.create_user(username="alice", email="a@chat.com", password="pass")
    recipient = User.objects.create_user(username="bob", email="b@chat.com", password="pass")
    chat = Chat.objects.create(sender=sender, recipient=recipient, content="Hello!")
    assert chat.content == "Hello!"
    assert chat.sender == sender
    assert chat.recipient == recipient
