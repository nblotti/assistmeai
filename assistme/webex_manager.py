import csv
import logging
import threading
import time
from multiprocessing import Queue

from urllib.request import urlretrieve

import requests
import json
from pathlib import Path

from ffmpeg import _ffmpeg
from numpy import floor
from openai import OpenAI

from assistme.firebase_manager import FirebaseManager
from assistme.models import Transcript

from assistmeai.config import webex_server, downloaded_filepath, OPEN_AI_KEY


class WebexManager:

    def __init__(self):
        self.url_list = webex_server + "recordings"
        self.url_detail = webex_server + "recordings/{recordingId}"
        self.client = OpenAI(api_key=OPEN_AI_KEY)


    def start_download(self,firebase_token,file_path,id,document_id,format):
        queue = Queue()
        t = threading.Thread(target=basic_worker, args=(queue,))
        t.daemon = True
        t.start()
        queue.put(firebase_token)
        queue.put(file_path)
        queue.put(id)
        queue.put(document_id)
        queue.put(format)
    def get_webex_recordings_url(self, auth_key):
        myResponse = requests.get(url_list, headers={'Authorization': "Bearer " + auth_key})
        if (myResponse.ok):
            jdata = json.loads(myResponse.content)

            for f in jdata['items']:
                detail_url = url_detail.format(recordingId=f['id'])
                detailResponse = requests.get(detail_url, headers={'Authorization': "Bearer " + auth_key})
                ddata = json.loads(detailResponse.content)
                f['directDownloadLink'] = ddata['temporaryDirectDownloadLinks']['recordingDownloadLink']
                downloaded_file_path = self.download_webex(f['directDownloadLink'], f['id'])
                content = self.get_transcript(downloaded_file_path)
                f['content'] = json.loads(content)['transcript']['transcript']
                Path.unlink(Path(downloaded_file_path))

            return json.dumps(jdata)
        else:
            myResponse.raise_for_status()

    def webex_meeting_detail(self,auth_key, pk):
        return pk

    def get_transcript(self,file):
        video = file[::-1].partition('/')[0]
        video = video[::-1]

        path = file[0:len(file) - len(video)]

        csv_file = video.partition('.')[0] + ".csv"

        video_file_path = path + video
        csv_file_path = path + csv_file

        transcripted = ""

        (_ffmpeg
         .input(video_file_path, vn=None)
         .output(path + video.partition('.')[0] + '_%d.mp3', f='segment', segment_time='600',
                 segment_list=csv_file_path)
         .run())

        with open(csv_file_path, newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in spamreader:
                current_audio_file_path = path + row[0]
                audio_file = open(current_audio_file_path, "rb")

                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                transcripted += transcript.text
                audio_file.close()

                Path.unlink(Path(current_audio_file_path))
        csvfile.close()

        data = {
            'file': file,
            'transcript': transcripted
        }
        Path.unlink(Path(csv_file_path))

        content = {}
        content['transcript'] = data
        json_data = json.dumps(content)
        return json_data

    def download(self,url):
        filename = url[::-1].partition('/')[0][::-1]
        urlretrieve(url, downloaded_filepath + filename)
        return downloaded_filepath + filename

    def download_webex(self,url, filename):
        now = str(floor(time.time() * 1000).astype(int))
        path = downloaded_filepath + now + filename
        print(path)
        urlretrieve(url, path)
        return path


    def basic_worker(self,queue):
        obj = None
        firebase_manager = FirebaseManager()
        while True:
            try:
                firebase_token = queue.get()
                file_path = queue.get()
                id_str = queue.get()
                document_id = queue.get()
                format_str = queue.get()
                obj = Transcript.objects.get(id=id_str)
                downloaded_file_path = self.download_webex(file_path, document_id + "." + format_str)

                setattr(obj, "status", Transcript.Statut.DOWNLOADED)
                obj.save()
                response = self.get_transcript(downloaded_file_path)
                setattr(obj, "content", response)
                setattr(obj, "status", Transcript.Statut.TRANSCRIBED)
                obj.save()
                Path.unlink(Path(downloaded_file_path))
                firebase_manager.send_firebase_notification(firebase_token, obj)
                setattr(obj, "status", Transcript.Statut.FIREBASE_SENT)
                obj.save()
                queue.task_done()
            except Exception as e:
                if obj:
                    setattr(obj, " error_data", e)
