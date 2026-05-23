import pytest
from pydantic import ValidationError
from botocore.exceptions import ClientError, ParamValidationError, NoCredentialsError, LoginError, ReadTimeoutError
from services import SQSService
from services.sqs import SQSServiceSettings
from services.sqs.models.entities import Message


def test_receive_messages_messages_success(settings: SQSServiceSettings) -> list[Message]:
    sqs_service = SQSService(
        host=settings.host,
        region=settings.region,
        queue_name=settings.queue_name,
        queue_url=settings.queue_url,
        access_key_id=settings.access_key_id,
        secret_access_key=settings.secret_access_key
    )

    messages = sqs_service.receive_messages()

    assert isinstance(messages, list)

    for m in messages:
        assert isinstance(m, Message)

    return messages

def test_receive_messages_messages_raises_error(settings: SQSServiceSettings):
    with pytest.raises((NoCredentialsError, LoginError, ReadTimeoutError)):
        sqs_service = SQSService(
            host=settings.host,
            region=settings.region,
            queue_name=settings.queue_name,
            queue_url=settings.queue_url,
            access_key_id=settings.access_key_id,
            secret_access_key=settings.secret_access_key
        )

        with pytest.raises((ValidationError, ClientError, ParamValidationError)):
            messages = sqs_service.receive_messages()
