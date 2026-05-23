from services.base import AuthCredentials
from pydantic import SecretStr


class SQSAuthCredentials(AuthCredentials):
    host: str
    region: str
    queue_name: str
    queue_url: str
    access_key_id: SecretStr
    secret_access_key: SecretStr
