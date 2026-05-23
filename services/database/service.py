import asyncio

from typing import Unpack

from loguru import logger
from asyncpg import connect as pg_connect
from asyncpg.protocol import Record
from asyncpg.connection import Connection as AsyncpgConnection
from asyncpg.exceptions import PostgresError, InterfaceError, InternalClientError

from services.base import BaseService

from .client import DatabaseAuthCredentials
from .models.entities import DEFAULT, BaseDatabaseEntity
from .exceptions import DatabaseException, DatabaseSelectException, DatabaseInsertException


class DatabaseService(BaseService):
    def __init__(self, **auth_credentials: Unpack[DatabaseAuthCredentials]) -> None:
        self._auth_credentials = auth_credentials

    async def start(self) -> None:
        try:
            self._connection: AsyncpgConnection = await pg_connect(
                host=self._auth_credentials['host'],
                port=self._auth_credentials['port'],
                user=self._auth_credentials['user'],
                password=self._auth_credentials['password'].get_secret_value(),
                database=self._auth_credentials['name'],
                loop=asyncio.get_running_loop()
            )
        except (PostgresError, InterfaceError, InternalClientError) as e:
            raise DatabaseException(f'{e.__class__.__name__}: {e}')

    async def get_entity[EntityType: BaseDatabaseEntity](self, entity_class: type[EntityType]) -> list[EntityType]:
        logger.info(f'{self.__class__.__name__}: Получение сущностей {entity_class.__name__}...')
        
        try:
            entity_records: list[Record] = await self._connection.fetch(f'SELECT * FROM {entity_class.__table_name__};')
        except (PostgresError, InterfaceError, InternalClientError) as e:
            logger.error((
                f'{self.__class__.__name__}: Не удалось получить сущности {entity_class.__name__}, '
                f'возникло исключение {e.__class__.__name__}({e}).'
            ))

            raise DatabaseSelectException(str(e))
        else:
            logger.info(f'{self.__class__.__name__}: Сущности ({len(entity_records)}) {entity_class.__name__} успешно получены.')
            return [entity_class(**entity_record) for entity_record in entity_records]

    async def insert_entity(self, entity: BaseDatabaseEntity) -> None:
        logger.info(f'{self.__class__.__name__}: Добавление сущности {entity.__class__.__name__}...')
        
        insert_values = []
        query_args = []

        for field_value in entity.model_dump().values():
            if field_value == DEFAULT:
                insert_values.append(DEFAULT)
            else:
                insert_values.append(f'${len(query_args)+1}')
                query_args.append(field_value)
        
        try:
            entity_id = await self._connection.fetchval(
                f'INSERT INTO {entity.__table_name__} VALUES ({', '.join(insert_values)}) RETURNING {entity.__table_primary_key__};',
                *query_args
            )
        except (PostgresError, InterfaceError, InternalClientError) as e:
            logger.error((
                f'{self.__class__.__name__}: Не удалось добавить сущность {entity.__class__.__name__}, '
                f'возникло исключение {e.__class__.__name__}({e}).'
            ))

            raise DatabaseInsertException(str(e)) 
        else:
            logger.info(f'{self.__class__.__name__}: Сущность {entity.__class__.__name__} (ID: {entity_id}) успешно добавлена.')

    async def exit(self) -> None:
        if hasattr(self, '_connection'):
            await self._connection.close()
