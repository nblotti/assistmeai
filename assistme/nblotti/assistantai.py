import json
import csv
import time

from ffmpeg import _ffmpeg
import ffmpeg
from numpy import floor
from openai import OpenAI
from urllib.request import urlretrieve
from pathlib import Path
from firebase_admin import messaging

client = OpenAI(api_key="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")

# downloaded_filepath = "/home/nblotti/test/"
downloaded_filepath = "/app/transcripts/"


def getTranscript(file):
    video = file[::-1].partition('/')[0]
    video = video[::-1]

    path = file[0:len(file) - len(video)]

    csv_file = video.partition('.')[0] + ".csv"

    video_file_path = path + video
    csv_file_path = path + csv_file

    transcripted = ""

    (_ffmpeg
     .input(video_file_path, vn=None)
     .output(path + video.partition('.')[0] + '_%d.mp3', f='segment', segment_time='600', segment_list=csv_file_path)
     .run())

    with open(csv_file_path, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in spamreader:
            current_audio_file_path = path + row[0]
            audio_file = open(current_audio_file_path, "rb")
            transcript = client.audio.transcriptions.create(
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


def sendFireBaseNotification(registration_token, obj):
    message = messaging.Message(
        data={
            'response': str(obj.id),
        },
        token=registration_token,
    )

    datastr = {
        'response': str(obj.id),
        'token': registration_token
    },
    setattr(obj, "firebase_message_data_sent", json.dumps(datastr))
    # Send a message to the device corresponding to the provided
    # registration token.
    try:
        response = messaging.send(message)
        setattr(obj, "firebase_message_result", json.dumps(response))
        obj.save()
    except Exception as e:
        print(e)
        setattr(obj, "error_data", e)
        obj.save


def download(url):
    filename = url[::-1].partition('/')[0][::-1]
    urlretrieve(url, downloaded_filepath + filename)
    return downloaded_filepath + filename


def downloadWebex(url, filename):
    now = str(floor(time.time() * 1000).astype(int))
    path = downloaded_filepath + now + filename
    print(path)
    urlretrieve(url, path)
    return path
