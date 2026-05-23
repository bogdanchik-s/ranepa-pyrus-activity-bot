import asyncio

from typing import Iterable, cast
from contextlib import suppress

from loguru import logger
from pydantic import ValidationError

from common.types import Seconds
from services import DatabaseService, SQSService
from services.database.models.entities import DB_PyrusTaskEvent
from services.pyrus.models.entities import ApprovalStep, TitleFormField, TableFormField, FormTaskComment
from services.sqs.models.entities import Message

from .models.entities import PyrusTaskEventInfo


class AppProcessManager:
    def __init__(self, database: DatabaseService, sqs: SQSService) -> None:
        self._database = database
        self._sqs = sqs
    
    async def _handle_pyrus_message(self, messages: Iterable[Message]) -> None:
        for message in messages:
            logger.info(f'[{self.__class__.__name__}]: Обработка события (Message ID: {message.id})...')
            
            try:
                pyrus_task_event_info = PyrusTaskEventInfo.model_validate_json(message.body or '')
            except ValidationError:
                logger.warning(f'[{self.__class__.__name__}]: Тело события (Message ID: {message.id}) не соответствует структуре {PyrusTaskEventInfo.__name__}.')
                self._sqs.delete_message(message)
                logger.info(f'[{self.__class__.__name__}]: Обработка события (Message ID: {message.id}) завершена.')

                continue

            field_updates = set()

            if isinstance(pyrus_task_event_info.comment, FormTaskComment):
                for field in pyrus_task_event_info.comment.field_updates or []:
                    match field:
                        case TitleFormField():
                            if field.value is None:
                                field_updates.add(f'[{field.id}] {field.name}')
                            else:
                                for title_field in field.value.fields:
                                    if isinstance(title_field, TableFormField):
                                        if title_field.value is None:
                                            field_updates.add(f'[{title_field.id}] {title_field.name}')
                                        else:
                                            for table_row in title_field.value:
                                                for table_cell in table_row.cells:
                                                    field_updates.add(f'[{field.id}:{table_cell.id}:{table_row.row_id}] {field.name}:{table_cell.name}:{table_row.row_id}')
                                    else:
                                        field_updates.add(f'[{title_field.id}] {title_field.name}')
                        
                        case TableFormField():
                            if field.value is None:
                                field_updates.add(f'[{field.id}] {field.name}')
                            else:
                                for table_row in field.value:
                                    for table_cell in table_row.cells:
                                        field_updates.add(f'[{field.id}:{table_cell.id}:{table_row.row_id}] {field.name}:{table_cell.name}:{table_row.row_id}')

            pyrus_task_event = DB_PyrusTaskEvent(
                datetime=pyrus_task_event_info.comment.create_date,
                task_id=pyrus_task_event_info.task_id,
                task_form=None if pyrus_task_event_info.form_id is None else f'[{pyrus_task_event_info.form_id}] {pyrus_task_event_info.form_name}',
                person=f'[{pyrus_task_event_info.comment.author.id}] {pyrus_task_event_info.comment.author.first_name} {pyrus_task_event_info.comment.author.last_name}',
                person_role={f'[{role.id}] {role.name}' for role in pyrus_task_event_info.comment.comment_as_roles or []},
                person_approval_choice=None if pyrus_task_event_info.comment.approval_choice is None else pyrus_task_event_info.comment.approval_choice.value,
                comment_id=pyrus_task_event_info.comment.id,
                comment_text=pyrus_task_event_info.comment.text,
                approvals_added={f'[{approving.person.id}] {approving.person.first_name} {approving.person.last_name}' for step in cast(list[ApprovalStep], getattr(pyrus_task_event_info.comment, 'approvals_added', []) or []) for approving in step},
                approvals_removed={f'[{approving.person.id}] {approving.person.first_name} {approving.person.last_name}' for step in cast(list[ApprovalStep], getattr(pyrus_task_event_info.comment, 'approvals_removed', []) or []) for approving in step},
                approvals_rerequested={f'[{approving.person.id}] {approving.person.first_name} {approving.person.last_name}' for step in cast(list[ApprovalStep], getattr(pyrus_task_event_info.comment, 'approvals_rerequested', []) or []) for approving in step},
                subscribers_added={f'[{person.id}] {person.first_name} {person.last_name}' for person in pyrus_task_event_info.comment.subscribers_added or []},
                subscribers_removed={f'[{person.id}] {person.first_name} {person.last_name}' for person in pyrus_task_event_info.comment.subscribers_removed or []},
                subscribers_rerequested={f'[{person.id}] {person.first_name} {person.last_name}' for person in pyrus_task_event_info.comment.subscribers_rerequested or []},
                field_updates=field_updates,
                action=None if pyrus_task_event_info.comment.action is None else pyrus_task_event_info.comment.action.value
            )

            try:
                await self._database.insert_entity(pyrus_task_event)
            except:
                logger.warning(f'[{self.__class__.__name__}]: Не удалось сохранить событие (Message ID: {message.id}) в базу данных.')
                logger.info(f'[{self.__class__.__name__}]: Обработка сообщения {message.id} завершена.')
                
                continue

            self._sqs.delete_message(message)

            logger.info(f'[{self.__class__.__name__}]: Обработка события (Message ID: {message.id}) завершена.')

    async def start_polling(self, interval: Seconds) -> None:        
        logger.info(f'[{self.__class__.__name__}]: Опрос событий запущен. Интервал: {interval} сек.')
                
        with suppress(asyncio.CancelledError):
            while True:
                messages = self._sqs.receive_messages()

                if len(messages) > 0:
                    await self._handle_pyrus_message(messages)
                
                logger.info(f'[{self.__class__.__name__}]: Время ожидания: {interval} сек.')
                await asyncio.sleep(interval)

        logger.info(f'[{self.__class__.__name__}]: Опрос событий остановлен.')
