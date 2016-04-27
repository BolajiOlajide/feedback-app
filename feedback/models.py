from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class BaseInfo(models.Model):
    """Base class containing all models common information."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Define Model as abstract."""

        abstract = True


class GoogleUser(models.Model):
    """Google OAuth User model defined"""

    google_id = models.CharField(max_length=60, unique=True)

    app_user = models.OneToOneField(User, related_name='user',
                                    on_delete=models.CASCADE)

    def __unicode__(self):
        return "%s %s" % (self.app_user.first_name,
                          self.app_user.last_name)


class SentFeedback(BaseInfo):
    """Sent feedback data model defined."""

    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    receiver = models.CharField(max_length=100)
    message = models.TextField()

    class Meta:
        ordering = ('-created_at',)

    def __unicode__(self):
        return "Sender {} and receiver {}" .format(self.sender.username,
                                                   self.receiver)


class ReceivedFeedback(BaseInfo):
    """Recieved feedback data model defined."""

    receiver = models.ForeignKey(User, on_delete=models.CASCADE)
    slack_username = models.CharField(max_length=100)
    message = models.TextField()

    class Meta:
        ordering = ('-created_at',)

    def __unicode__(self):
        return "Receiver {}" .format(self.receiver.username)
