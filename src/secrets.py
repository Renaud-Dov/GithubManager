from base64 import b64encode
from src.header import get_headers
import requests
from nacl import encoding, public


def encrypt(public_key: str, secret_value: str) -> str:
    """Encrypt a Unicode string using the public key."""
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def get_public_key(repo: str):
    headers = get_headers()
    response = requests.get(f"https://api.github.com/repos/Renaud-Dov/{repo}/actions/secrets/public-key",
                            headers=headers)
    return response.json()["key"]


def create_secret(repo,secret_name,secret_value):
    headers = get_headers()
    data = dict(encrypted_value=encrypt(get_public_key(repo), secret_value))
    response = requests.put(
        f"https://api.github.com/repos/Renaud-Dov/{repo}/actions/secrets/{secret_name}",
        headers=headers,
        data=data)
    return response
