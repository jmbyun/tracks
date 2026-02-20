import json

from .config import settings


class Vault:
    def __init__(self):
        self.vault_path = settings.VAULT_PATH

    def to_dict(self):
        with open(self.vault_path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    def get(self, key):
        return self.to_dict().get(key, None)


vault = Vault()