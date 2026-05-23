import pytest
from asyncpg.exceptions import PostgresError, InterfaceError, InternalClientError
from botocore.exceptions import NoCredentialsError, LoginError, ReadTimeoutError
from pydantic import ValidationError
from services import SQSService, DatabaseService
from services.sqs import SQSServiceSettings
from services.sqs.models.entities import Message
from services.database import DatabaseServiceSettings
from core.process_manager import AppProcessManager


async def test_handle_pyrus_message_none_success(sqs_settings: SQSServiceSettings, database_settings: DatabaseServiceSettings) -> None:
    core = AppProcessManager(
        database=DatabaseService(
            host=database_settings.host,
            port=database_settings.port,
            user=database_settings.user,
            password=database_settings.password,
            name=database_settings.name
        ),
        sqs=SQSService(
            host=sqs_settings.host,
            region=sqs_settings.region,
            queue_name=sqs_settings.queue_name,
            queue_url=sqs_settings.queue_url,
            access_key_id=sqs_settings.access_key_id,
            secret_access_key=sqs_settings.secret_access_key
        )
    )

    message = Message(
        id='efeweaergare',
        body='{"data": "Bogdan Zakharov"}'
    )

    result = await core._handle_pyrus_message((message,))

    assert result is None


async def test_handle_pyrus_message_raises_error(sqs_settings: SQSServiceSettings, database_settings: DatabaseServiceSettings) -> None:
    with pytest.raises((NoCredentialsError, LoginError, ReadTimeoutError, PostgresError, InterfaceError)):
        core = AppProcessManager(
            database=DatabaseService(
                host=database_settings.host,
                port=database_settings.port,
                user=database_settings.user,
                password=database_settings.password,
                name=database_settings.name
            ),
            sqs=SQSService(
                host=sqs_settings.host,
                region=sqs_settings.region,
                queue_name=sqs_settings.queue_name,
                queue_url=sqs_settings.queue_url,
                access_key_id=sqs_settings.access_key_id,
                secret_access_key=sqs_settings.secret_access_key
            )
        )


        with pytest.raises(ValidationError):
            message = Message(
                id=3433564,
                body='{"data": "Bogdan Zakharov"}'
            )

            with pytest.raises((PostgresError, InterfaceError, InternalClientError)):
                result = await core._handle_pyrus_message((message,))
