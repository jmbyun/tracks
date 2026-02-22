import base64
import json

class SecretStorage:
    def __init__(self):
        # TODO (Instagram Integration):
        # Decode the base64 string below, add the following keys to the JSON object, 
        # and then re-encode it to base64:
        # "INSTAGRAM_CLIENT_ID": "<Your Meta App ID>"
        # "INSTAGRAM_CLIENT_SECRET": "<Your Meta App Secret>"
        
        # TODO (Twitter/X Integration):
        # Add the following keys to the JSON object:
        # "TWITTER_CLIENT_ID": "<Your Twitter Client ID>"
        # "TWITTER_CLIENT_SECRET": "<Your Twitter Client Secret>"

        # TODO (SmartThings Integration):
        # Add the following keys to the JSON object:
        # "SMARTTHINGS_CLIENT_ID": "<Your SmartThings Client ID>"
        # "SMARTTHINGS_CLIENT_SECRET": "<Your SmartThings Client Secret>"

        # TODO (YouTube Integration):
        # Add the following keys to the JSON object:
        # "YOUTUBE_CLIENT_ID": "<Your YouTube Client ID>"
        # "YOUTUBE_CLIENT_SECRET": "<Your YouTube Client Secret>"
        self.source = "ewogICAgIkdPT0dMRV9DTElFTlRfSUQiOiAiODA2MzAzNjMwNzIzLXQ4NnFtcjJidmcxYnEzMjU1Z2VqZHBib3M4ajNub3BhLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwKICAgICJHT09HTEVfQ0xJRU5UX1NFQ1JFVCI6ICJHT0NTUFgtVy1OUi1VcWlNRkhhZWdhdEdJQUtGUjNjQkQ1QSIKfQ=="
        self.secrets = json.loads(base64.b64decode(self.source))

    def to_dict(self):
        return self.secrets

    def get(self, key):
        return self.secrets.get(key)

secret = SecretStorage()