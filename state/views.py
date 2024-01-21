# Create your views here.
import json

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser


from state.statemachine.CommandControl import CommandControl


@api_view(['POST'])
@parser_classes([JSONParser])
def get_command(request):
    control = CommandControl()


    wbx_jwt_token = request.META.get('HTTP_WBXJWTTOKEN')
    firebase_token = request.META.get('HTTP_FIREBASETOKEN')


    control.do_check_command(request.data["messages"],wbx_jwt_token,firebase_token)

    if control.current_state == CommandControl.error_state:
        return HttpResponse("", content_type="application/json", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    control.do_start_process()

    print("---------------------------------------------------------------------------")
    print("state calculated : " + control.current_state.value)
    print("---------------------------------------------------------------------------")

    if control.current_state == CommandControl.memo_state:
        control.do_memo()
    elif control.current_state == CommandControl.client_state:
        control.do_client()
    elif control.current_state == CommandControl.query_state:
        control.do_query()
    elif control.current_state == CommandControl.load_webex_state:
        control.do_load_webex_command()
    elif control.current_state == CommandControl.speech_to_text_state:
        control.do_speach_to_text_command()
    elif control.current_state == CommandControl.load_stock_quotes_state:
        control.do_load_stock_quotes_command()
    elif control.current_state == CommandControl.clear_state:
        control.do_clear()

    print("---------------------------------------------------------------------------")
    print("state" + control.current_state.value)
    print("---------------------------------------------------------------------------")
    if control.current_state == CommandControl.error_state:
        return HttpResponse("", content_type="application/json", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return HttpResponse(json.dumps(control.data), content_type="application/json", status=status.HTTP_200_OK)
