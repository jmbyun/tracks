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

    def set(self, key, value):
        data = self.to_dict()
        data[key] = value
        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def delete(self, key):
        data = self.to_dict()
        if key in data:
            del data[key]
            with open(self.vault_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)


vault = Vault()