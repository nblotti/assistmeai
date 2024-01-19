from django.db import models
from django.utils.translation import gettext_lazy as _


# Create your models here.

class TranscriptManager(models.Manager):
    def create_transcript(self, document_id, fire_base_token):
        transcript = self.create(document_id=document_id, status=Transcript.Statut.RECEIVED,
                                 fire_base_token=fire_base_token)
        # do something with the book
        return transcript


class Transcript(models.Model):
    class Statut(models.TextChoices):
        RECEIVED = '1', _('Received')
        DOWNLOADED = '2', _('Downloaded')
        TRANSCRIBED = '3', _('Transcribed')
        FIREBASE_SENT = '4', _('FirebaseSent')

    id = models.AutoField(primary_key=True, editable=False)
    document_id = models.CharField(max_length=50)
    content = models.TextField()
    status = models.CharField( max_length=2, choices=Statut.choices, default=Statut.RECEIVED)
    fire_base_token = models.CharField(max_length=50)
    firebase_message_data_sent = models.TextField(default=None, blank=True, null=True)
    firebase_message_result = models.TextField(default=None, blank=True, null=True)
    error_data = models.TextField(default=None, blank=True, null=True)

    objects = TranscriptManager()
