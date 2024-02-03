import json

from firebase_admin import messaging


class FirebaseManager:

    def initialize(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)

    def send_firebase_notification(self,registration_token, obj):
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
