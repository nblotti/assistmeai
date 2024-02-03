import logging
import sys
from django.contrib.auth.models import Group, User
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser

from assistme.command_controller import CommandController
from assistme.firebase_manager import FirebaseManager
from assistme.models import Transcript
from assistme.serializers import GroupSerializer, UserSerializer, TranscriptSerializer
from assistme.webex_manager import WebexManager
from pathlib import Path

from assistme.command_manager import CommandManager

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


@api_view(['POST'])
@parser_classes([JSONParser])
def do_command(request):
    return CommandController(logger).do_command(request)


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


@api_view(['POST'])
@parser_classes([JSONParser])
def request_text_to_speach(request):
    if request.method == 'POST':
        firebase_token = request.META.get('HTTP_FIREBASETOKEN')
        if not firebase_token:
            return HttpResponse("{\"response\":\"HTTP_FIREBASETOKEN not present\"}",
                                content_type="application/json", status=status.HTTP_401_UNAUTHORIZED)

        firebase_manager = FirebaseManager()
        webex_manager = WebexManager()

        firebase_manager.initialize()
        document_path = request.data["url"]
        webex_id = request.data["id"]
        document_id = request.data["document_id"]
        document_format = request.data["format"]

        webex_manager.start_download(firebase_token, document_path, webex_id, document_id, document_format)

        return HttpResponse("{\"response\":\"ok\"}", content_type="application/json", status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([JSONParser])
def document(request):
    if request.method == 'POST':
        webex_manager = WebexManager()
        file_path = request.data["url"]
        file_ = request.data["id"]
        downloaded_file_path = webex_manager.download_webex(file_path, file_)
        response = webex_manager.get_transcript(downloaded_file_path)
        Path.unlink(Path(downloaded_file_path))

        return HttpResponse(response, content_type="application/json", status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([JSONParser])
def webex_meetings(request):
    if request.method == 'POST':
        webex_manager = WebexManager()
        auth_key = request.data['auth_key']
        response = webex_manager.get_webex_recordings_url(auth_key)
        return HttpResponse(response, content_type="application/json", status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([JSONParser])
def webex_meeting_detail(request, pk):
    if request.method == 'POST':
        auth_key = request.data['auth_key']

        webex_manager = WebexManager()
        response = webex_manager.webex_meeting_detail(auth_key, pk)
        return HttpResponse(response, content_type="application/json", status=status.HTTP_200_OK)
