# Create your views here.
import json
import logging
import sys
import time

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser


from state.statemachine.CommandControl import CommandControl

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
# This retrieves a Python logging instance (or creates it)
logger = logging.getLogger(__name__)

@api_view(['POST'])
@parser_classes([JSONParser])
def get_command(request):
    control = CommandControl()

    start = time.time()
    wbx_jwt_token = request.META.get('HTTP_WBXJWTTOKEN')
    firebase_token = request.META.get('HTTP_FIREBASETOKEN')


    control.do_check_command(request.data["messages"],wbx_jwt_token,firebase_token)

    if not control.in_error:
        control.run_command()

    end = time.time()

    logger.debug("---------------------------------------------------------------------------")
    logger.debug("Elapsed time for global query : {0}".format(end - start))
    logger.debug("---------------------------------------------------------------------------")

    return HttpResponse(json.dumps(control.data), content_type="application/json", status=status.HTTP_200_OK)
