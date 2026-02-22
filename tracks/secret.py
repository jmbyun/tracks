import base64
import json

class SecretStorage:
    def __init__(self):
        self.source = "ewogICAgIkdPT0dMRV9DTElFTlRfSUQiOiAiODA2MzAzNjMwNzIzLXQ4NnFtcjJidmcxYnEzMjU1Z2VqZHBib3M4ajNub3BhLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwKICAgICJHT09HTEVfQ0xJRU5UX1NFQ1JFVCI6ICJHT0NTUFgtVy1OUi1VcWlNRkhhZWdhdEdJQUtGUjNjQkQ1QSIKfQ=="
        self.secrets = json.loads(base64.b64decode(self.source))

    def to_dict(self):
        return self.secrets

    def get(self, key):
        return self.secrets.get(key)

secret = SecretStorage()