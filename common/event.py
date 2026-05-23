from typing import Self, TypeAlias, Any, Concatenate
from collections.abc import Callable


EventName: TypeAlias = str


class Event[**EventHandlerParamSpec]:
    """
    Класс события
    """


    def __init__(
        self,
        name: EventName,
        emit_handler: Callable[Concatenate[EventName, EventHandlerParamSpec], bool],
        add_listener_handler: Callable[[EventName, Callable[EventHandlerParamSpec, Any]], Callable[EventHandlerParamSpec, Any]],
        remove_listener_handler: Callable[[EventName, Callable[EventHandlerParamSpec, Any]], None]
    ) -> None:
        self._name = name
        self._emit_handler = emit_handler
        self._add_listener_handler = add_listener_handler
        self._remove_listener_handler = remove_listener_handler
    
    @property
    def name(self) -> EventName:
        return self._name

    def emit(self, *args: EventHandlerParamSpec.args, **kwargs: EventHandlerParamSpec.kwargs) -> bool:
        return self._emit_handler(self.name, *args, **kwargs)

    def add_listener(self, handler: Callable[EventHandlerParamSpec, Any]) -> Callable[EventHandlerParamSpec, Any]:
        if not isinstance(handler, Callable):
            ValueError(f'[{self.__class__.__name__}] The event handler must be a `Callable` instance.')
        
        return self._add_listener_handler(self.name, handler)

    def remove_listener(self, handler: Callable[EventHandlerParamSpec, Any]) -> None:
        return self._remove_listener_handler(self.name, handler)

    def __iadd__(self, handler: Callable[EventHandlerParamSpec, Any]) -> Self:
        if not isinstance(handler, Callable):
            ValueError(f'[{self.__class__.__name__}] The event handler must be a `Callable` instance.')
        
        self.add_listener(handler)

        return self
    
    def __isub__(self, handler: Callable[EventHandlerParamSpec, Any]) -> Self:
        self.remove_listener(handler)
        return self

    def __str__(self) -> str:
        return self.name
