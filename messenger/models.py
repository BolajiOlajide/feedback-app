from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class BaseModel(models.Model):
    """
    Defines common fields in the model classes.
    """
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Conversation(BaseModel):
    """
    Represents a thread of messages exchanged between
    multiple users.
    """
    subject = models.CharField(max_length=128)
    initiator = models.ForeignKey(
        User,
        related_name='initiated_conversations'
    )
    members = models.ManyToManyField(
        User,
        related_name='conversations'
    )

    @property
    def latest_message(self):
        return  self.messages.order_by('date_created').last()




class Message(BaseModel):
    """
    Represents a post by a user to the other members
    of a conversation
    """
    content = models.TextField('')
    user = models.ForeignKey(User, related_name='+')
    success = models.BooleanField(default=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
