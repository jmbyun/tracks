import base64
import json

class SecretStorage:
    def __init__(self):
        # TODO (Instagram Integration):
        # Decode the base64 string below, add the following keys to the JSON object, 
        # and then re-encode it to base64:
        # "INSTAGRAM_CLIENT_ID": "<Your Meta App ID>"
        # "INSTAGRAM_CLIENT_SECRET": "<Your Meta App Secret>"
        self.source = "ewogICAgIkdPT0dMRV9DTElFTlRfSUQiOiAiODA2MzAzNjMwNzIzLXQ4NnFtcjJidmcxYnEzMjU1Z2VqZHBib3M4ajNub3BhLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwKICAgICJHT09HTEVfQ0xJRU5UX1NFQ1JFVCI6ICJHT0NTUFgtVy1OUi1VcWlNRkhhZWdhdEdJQUtGUjNjQkQ1QSIKfQ=="
        self.secrets = json.loads(base64.b64decode(self.source))

    def to_dict(self):
        return self.secrets

    def get(self, key):
        return self.secrets.get(key)

secret = SecretStorage()