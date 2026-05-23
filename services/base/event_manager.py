from abc import ABC
from typing import Self, Any, get_origin
from pyee.base import EventEmitter

from common.event import Event


class ServiceEventManagerMixin[EventEmitterType: EventEmitter](ABC):
    """
    Класс событий сервиса
    """

    __event_emitter__: EventEmitterType


    @classmethod
    def _register_events(cls) -> None:
        for event_name, event_class in cls.__annotations__.items():
            if (get_origin(event_class) or event_class) is Event:
                if event_name in cls.__event_emitter__.event_names():
                    continue

                event = event_class(
                    name=event_name,
                    emit_handler=cls.__event_emitter__.emit,
                    add_listener_handler=cls.__event_emitter__.add_listener,
                    remove_listener_handler=cls.__event_emitter__.remove_listener
                )

                # Добавляем обработчик события в EventEmitter,
                # чтобы новое событие было зарегистрировано
                cls.__event_emitter__.once(event.name, lambda *args, **kwargs: None)

                setattr(cls, event_name, event)

    def __new__(cls, *args, **kwargs) -> Self:
        cls = super().__new__(cls)
        cls._register_events()
        return cls

    def __class_getitem__(cls, typevar_values: type[Any] | tuple[type[Any], ...]) -> type[Self]:
        if not isinstance(typevar_values, tuple):
            typevar_values = (typevar_values,)

        for typevar_value in typevar_values:
            if issubclass(typevar_value, EventEmitter):
                cls.__event_emitter__ = typevar_value() # type: ignore
                break

        return cls
