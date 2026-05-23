import pytest
from pydantic import ValidationError
from asyncpg.exceptions import PostgresError, InterfaceError, InternalClientError
from services.database import DatabaseService, DatabaseServiceSettings
from services.database.models.entities import DB_PyrusTaskEvent


async def test_insert_entity_none_success(settings: DatabaseServiceSettings) -> None:
    database = DatabaseService(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        name=settings.name
    )

    entity = DB_PyrusTaskEvent(
        task_id=123424,
        person='Богдан Захаров',
        comment_id=22345434
    )

    result = await database.insert_entity(entity)

    assert result is None


async def test_insert_entity_raises_error(settings: DatabaseServiceSettings) -> None:
    with pytest.raises((PostgresError, InterfaceError)):
        database = DatabaseService(
            host=settings.host,
            port=settings.port,
            user=settings.user,
            password=settings.password,
            name=settings.name
        )

        with pytest.raises(ValidationError):
            entity = DB_PyrusTaskEvent(
                task_id=123424,
                person=123433234,
                comment_id=22345434,
            )

            with pytest.raises((PostgresError, InterfaceError, InternalClientError)):
                result = await database.insert_entity(entity)
