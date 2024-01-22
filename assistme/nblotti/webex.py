import requests
import json
from assistme.nblotti.assistantai import getTranscript, downloadWebex
from pathlib import Path

from djangoProject.config import webex_server

url_list = webex_server + "recordings"
url_detail = webex_server + "recordings/{recordingId}"


def getWebexRecordingsUrl(auth_key):
    myResponse = requests.get(url_list, headers={'Authorization': "Bearer " + auth_key})
    # print (myResponse.status_code)

    # For successful API call, response code will be 200 (OK)
    if (myResponse.ok):

        # Loading the response data into a dict variable
        # json.loads takes in only binary or string variables so using content to fetch binary content
        # Loads (Load String) takes a Json file and converts into python data structure (dict or list, depending on JSON)

        jdata = json.loads(myResponse.content)

        for f in jdata['items']:
            detail_url = url_detail.format(recordingId=f['id'])
            detailResponse = requests.get(detail_url, headers={'Authorization': "Bearer " + auth_key})
            ddata = json.loads(detailResponse.content)
            f['directDownloadLink'] = ddata['temporaryDirectDownloadLinks']['recordingDownloadLink']
            downloaded_file_path = downloadWebex(f['directDownloadLink'], f['id'])
            content = getTranscript(downloaded_file_path)
            f['content'] = json.loads(content)['transcript']['transcript']
            Path.unlink(Path(downloaded_file_path))

        return json.dumps(jdata)
    else:
        # If response code is not ok (200), print the resulting http error code with description
        myResponse.raise_for_status()


def webex_meeting_detail(auth_key, pk):
    return pk
