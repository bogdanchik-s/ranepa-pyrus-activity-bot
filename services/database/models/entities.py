from abc import ABC
from datetime import datetime, timezone
from typing import Any, Optional, Literal, TypeAlias, ClassVar, Sequence

from pydantic import (
    Field, AwareDatetime,
    model_validator, field_validator, ValidatorFunctionWrapHandler,
    field_serializer, SerializerFunctionWrapHandler\
)

from services.base.models.entities import BaseServiceEntity


EntityPropertyName: TypeAlias = str
DatabaseTableColumnName: TypeAlias = str

DEFAULT = 'DEFAULT'


class BaseDatabaseEntity(BaseServiceEntity, ABC):
    __table_name__: ClassVar[str]
    __table_primary_key__: ClassVar[str]


    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: dict[Any, Any]) -> None:
        unspecified_attrs = []

        for class_var_name in cls.__class_vars__:
            if hasattr(cls, class_var_name) and kwargs.get(class_var_name, None):
                raise ValueError(
                    f'[{cls.__name__}] The attribute value can be set once: in the description of the class structure, or in its key arguments.'
                )

            class_var_value = getattr(cls, class_var_name, kwargs.get(class_var_name, None))

            if class_var_value is None:
                unspecified_attrs.append(class_var_name)
            else:
                setattr(cls, class_var_name, class_var_value)

        if unspecified_attrs:
            raise AttributeError(f'[{cls.__name__}] The class attributes ({", ".join(unspecified_attrs)}) must be set.')


class DB_PyrusTaskEvent(BaseDatabaseEntity):
    __table_name__: ClassVar[str] = 'pyrus_task_event'
    __table_primary_key__: ClassVar[str] = 'id'


    id: int = Field(default=..., title='Идентификатор')
    datetime: AwareDatetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc), validate_default=True, title='Дата и время')
    task_id: int = Field(title='Номер задачи')
    task_form: Optional[str] = Field(default=None, title='Форма задачи')
    person: str = Field(title='Пользователь')
    person_role: Optional[set[str]] = Field(default=None, title='Роли пользователя')
    person_approval_choice: Optional[Literal['approved', 'rejected', 'acknowledged', 'revoked', 'waiting']] = Field(default=None, title='Статус согласования пользователя')
    comment_id: int = Field(title='Идентификатор комментария')
    comment_text: Optional[str] = Field(default=None, title='Текст комментария')
    approvals_added: Optional[set[str]] = Field(default=None, title='Добавленные согласующие')
    approvals_removed: Optional[set[str]] = Field(default=None, title='Удаленные согласующие')
    approvals_rerequested: Optional[set[str]] = Field(default=None, title='Перезапрошенные согласующие')
    subscribers_added: Optional[set[str]] = Field(default=None, title='Добавленные наблюдатели')
    subscribers_removed: Optional[set[str]] = Field(default=None, title='Удаленные наблюдатели')
    subscribers_rerequested: Optional[set[str]] = Field(default=None, title='Перезапрошенные наблюдатели')
    field_updates: Optional[set[str]] = Field(default=None, title='Обновленные поля формы')
    action: Optional[Literal['finished', 'reopened']] = Field(default=None, title='Действие')

    @model_validator(mode='before')
    @classmethod
    def check_id_not_present(cls, data: Any) -> Any:
        if isinstance(data, dict) and 'id' not in data:
            data['id'] = DEFAULT
        
        return data

    @field_validator('id', mode='wrap')
    @classmethod
    def id_validator(cls, value: Any, handler: ValidatorFunctionWrapHandler):
        return value if value == DEFAULT else handler(value)

    @field_serializer('id', mode='wrap', when_used='always')
    def id_serializer(self, value: Any, nxt: SerializerFunctionWrapHandler):
        return value if value == DEFAULT else nxt(value)

    @field_validator('*', mode='wrap')
    @classmethod
    def set_validator(cls, value: Any, handler: ValidatorFunctionWrapHandler):
        return handler(None) if isinstance(value, set) and len(value) == 0 else handler(value)
