import json
import time

from django.http import HttpResponse
from rest_framework import status

from assistme.command_manager import CommandManager


class CommandController:
    # class variable

    def __init__(self, logger):
        self.command_manager = CommandManager()
        self.logger = logger

    def do_command(self, request):
        start = time.time()
        wbx_jwt_token = request.META.get('HTTP_WBXJWTTOKEN')
        firebase_token = request.META.get('HTTP_FIREBASETOKEN')
        domain_header = request.META.get('HTTP_DOMAINHEADER')
        if domain_header is None:
            domain_header = ""

        self.command_manager.do_check_command(request.data["messages"], wbx_jwt_token, firebase_token,domain_header)

        if not self.command_manager.in_error:
            self.command_manager.run_command()

        end = time.time()

        self.logger.debug("---------------------------------------------------------------------------")
        self.logger.debug("Elapsed time for global query : {0}".format(end - start))
        self.logger.debug("---------------------------------------------------------------------------")

        return HttpResponse(json.dumps(self.command_manager.data), content_type="application/json", status=status.HTTP_200_OK)
