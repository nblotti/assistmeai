import json
import threading
from queue import Queue

import firebase_admin
from firebase_admin import credentials
from django.contrib.auth.models import Group, User
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser

from assistme.models import Transcript
from assistme.serializers import GroupSerializer, UserSerializer, TranscriptSerializer
from assistme.nblotti.assistantai import getTranscript, download, downloadWebex, sendFireBaseNotification
from assistme.nblotti.webex import getWebexRecordingsUrl
from pathlib import Path


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class TranscriptViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Transcript.objects.all()
    serializer_class = TranscriptSerializer


def basic_worker(queue):

    obj = None

    while True:
        try:
            firebase_token = queue.get()
            file_path = queue.get()
            id_str = queue.get()
            document_id = queue.get()
            format_str = queue.get()
            obj = Transcript.objects.get(id=id_str)
            downloaded_file_path = downloadWebex(file_path, document_id +"." + format_str)

            setattr(obj, "status", Transcript.Statut.DOWNLOADED)
            obj.save()
            response = getTranscript(downloaded_file_path)
            setattr(obj, "content", response)
            setattr(obj, "status", Transcript.Statut.TRANSCRIBED)
            obj.save()
            Path.unlink(Path(downloaded_file_path))
            sendFireBaseNotification(firebase_token,obj)
            setattr(obj, "status", Transcript.Statut.FIREBASE_SENT)
            obj.save()
            queue.task_done()
        except Exception as e:
            if obj:
                setattr(obj, " error_data", e)

@api_view(['POST'])
@parser_classes([JSONParser])
def requesttexttospeach(request):
    if request.method == 'POST':


        if not firebase_admin._apps:
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)

        firebase_token = request.META.get('HTTP_FIREBASETOKEN')
        queue = Queue()
        t = threading.Thread(target=basic_worker, args=(queue,))
        t.daemon = True
        t.start()
        file_path = request.data["url"]
        id = request.data["id"]
        document_id = request.data["document_id"]
        format = request.data["format"]

        queue.put(firebase_token)
        queue.put(file_path)
        queue.put(id)
        queue.put(document_id)
        queue.put(format)


        return HttpResponse("{\"response\":\"ok\"}",content_type="application/json", status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([JSONParser])
def document(request):
    if request.method == 'POST':
        file_path = request.data["url"]
        file_ = request.data["id"]
        downloaded_file_path = downloadWebex(file_path,file_)
        response = getTranscript(downloaded_file_path)
        Path.unlink(Path(downloaded_file_path))
        return HttpResponse(response,content_type="application/json", status=status.HTTP_200_OK)

@api_view(['POST'])
@parser_classes([JSONParser])
def webex_meetings(request):
    if request.method == 'POST':
        auth_key = request.data['auth_key']
        response = getWebexRecordingsUrl(auth_key)
        return HttpResponse(response, content_type="application/json", status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([JSONParser])
def webex_meeting_detail(request, pk):
    if request.method == 'POST':
        auth_key = request.data['auth_key']
        response = webex_meeting_detail(auth_key,pk)
        return HttpResponse(response, content_type="application/json", status=status.HTTP_200_OK)

