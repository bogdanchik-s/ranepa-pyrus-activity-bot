from abc import ABC
from collections.abc import Callable
from typing import Any, ClassVar, Unpack
from http import HTTPMethod
from yarl import URL
from aiohttp import ClientRequest, ClientResponse, ClientHandlerType
from pydantic import BaseModel, ConfigDict, Secret, SecretBytes, SecretStr, field_serializer

from .responses import BaseServiceResponse, BaseServiceErrorResponse


class BaseServiceRequest[ResponseType: BaseServiceResponse, ErrorResponseType: BaseServiceErrorResponse](BaseModel, ABC):
    """
    Базовый класс запроса к сервису
    """
    
    _response_class: ClassVar
    _error_response_class: ClassVar

    @property
    def __response_class__(self) -> type[ResponseType]:
        """
        Возвращает класс ответа от сервиса
        """

        # NOTE: Атрибут сделан через `@property` в целях
        # правильной работы статичных анализаторов типа,
        # так как `ClassVar` не может содержать в себе `TypeVar`

        return self._response_class

    @property
    def __error_response_class__(self) -> type[ErrorResponseType]:
        return self._error_response_class


    http_method: ClassVar[HTTPMethod]
    base_url: ClassVar[URL]
    endpoint: ClassVar[URL]

    @property
    def url(self) -> URL:
        """Возвращает полный URL с заполненными шаблонными подстроками

        Returns:
            URL: URL
        """
        
        base_path = self.base_url.path.format(**{
            field_name: field_value if not isinstance(field_value, (Secret, SecretBytes, SecretStr)) else field_value.get_secret_value()
            for field_name, field_value in self.__dict__.items()
        })
        
        endpoint = self.endpoint.path_qs.format(**{
            field_name: field_value if not isinstance(field_value, (Secret, SecretBytes, SecretStr)) else field_value.get_secret_value()
            for field_name, field_value in self.__dict__.items()
        })

        return self.base_url.with_path(base_path).joinpath(endpoint.strip('/'))

    @field_serializer('*', mode='wrap', when_used='json')
    def secret_fields_serializer(self, field_value: Any, default_serializer: Callable) -> Any:
        if isinstance(field_value, (Secret, SecretBytes, SecretStr)):
            return field_value.get_secret_value()
        else:
            return default_serializer(field_value)

    async def middleware(self, client_request: ClientRequest, client_handler: ClientHandlerType) -> ClientResponse:
        """
        Middleware (aiohttp.ClientMiddlewareType) для подготовки запроса к отправке.

        Например, используя данный метод можно добавить к запрос полезную нагрузку,
        установить нужные заголовки или куки.
        """
        
        await client_request.update_body(self.model_dump_json(by_alias=True, exclude_none=True, exclude_unset=True))

        return await client_handler(client_request)

    @classmethod
    def __init_subclass__(cls, **kwargs: Unpack[ConfigDict]):
        """
        Переопределение этого метода необходимо, ибо при наследовании возникает ошибка,
        несмотря на то что данный метод определен в базом классе модели `pydantic.main.BaseModel`:
        
        >>> TypeError: TestRequest.__init_subclass__() takes no keyword arguments

        Данный метод убирает все лишние `TypeVar` типа `BaseServiceResponse`,
        которые могут использоваться для передачи типа ответа в главный базовый класс запроса,
        то есть в `BaseServiceRequest`. Подобная реализация выглядит примерно следующим образом:

        >>> class BaseFooResponse(BaseServiceResponse):
        >>>     pass

        >>> class SomeFooResponse(BaseFooResponse):
        >>>     pass

        >>> class BaseFooRequest[FooResponseType: BaseFooResponse](BaseServiceRequest[FooResponseType]):
        >>>     pass

        >>> class SomeFooRequest(BaseFooRequest[SomeFooResponse]):
        >>>     pass
        
        Таким образом появляется второй уровень базовых классов запроса и ответа.
        Благодаря перменной типа `FooResponseType` статический анализатор типа работает правильно,
        и тип ответа передается в главный базовый класс запроса, то есть в `BaseServiceRequest`,
        однако в такой реализации внутри у нас появлется вторая переменная типа, то есть:

        >>> typing.Generic[FooResponseType, ResponseType]

        В связи чем при наследовании будет появляется ошибка, говорящая о том, что вторая переменная
        не указана:
        
        >>> TypeError: All parameters must be present on typing.Generic; you should inherit from typing.Generic[FooResponseType, ResponseType].

        Поэтому необходимо удалить переменную типа `FooResponseType`, оставив только одну главную переменную типа ответа,
        а именно `ResponseType`, которая объявлена в главном базовом классе запроса, то есть в `BaseServiceRequest`.
        """

        # print(cls.__name__, cls.__pydantic_generic_metadata__)

        for parameter in cls.__pydantic_generic_metadata__['parameters']:            
            if parameter is ResponseType or parameter is ErrorResponseType:
                continue

            if (issubclass(parameter.__bound__ or type(None), (
                ResponseType.__bound__ or type(None),
                ErrorResponseType.__bound__ or type(None)
            ))):
                cls.__pydantic_generic_metadata__['parameters'] = tuple(filter(
                    lambda p: p is not parameter,
                    cls.__pydantic_generic_metadata__['parameters']
                ))

            # if parameter is ResponseType:
            #     continue
            
            # parameter_types = get_args(parameter.__bound__) or (parameter.__bound__ or type(None),)
            # response_types = get_args(ResponseType.__bound__) or (ResponseType.__bound__ or type(None),)

            # if all(issubclass(parameter_type, response_type) for parameter_type, response_type in zip(parameter_types, response_types)):
            #     cls.__pydantic_generic_metadata__['parameters'] = tuple(filter(
            #         lambda p: p is not parameter,
            #         cls.__pydantic_generic_metadata__['parameters']
            #     ))

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: dict[Any, Any]) -> None:
        """
        Метод обрабатывает и валидирует переданные ключевые аргументы класса,
        которые используются для инициализации атрибутов класса.

        Данный метод вызывается `Pydantic` уже после инициализации всей модели
        в конце метода `__new__` метакласса
        """

        if cls.__name__.startswith('Base'):
            """
            NOTE: По каким-то причинам при использовании Generic'а в наследовании класса,
            то есть при:

            >>> class TestRequest(BaseServiceRequest[TestResponse]):
                                                     ^^^^^^^^^^^^

            метод BaseServiceRequest.__init_subclass__ вызывается дважды с разным __mro__ класса,
            если же не использовать Generic в наследовании, то нижеописанной ситуации не возникает.
            
            При первом вызове BaseServiceRequest.__init_subclass__ значение атрибута __mro__ выглядит так:
            
            >>> (
            >>>    <class 'services.base.models.requests.BaseServiceRequest[TestResponse]'>,
            >>>    <class 'services.base.models.requests.BaseServiceRequest'>,
            >>>    ...
            >>> )
            
            и при этом клюевые аргументы, переданные при наследовании, то есть:
            
            >>> class TestRequest(BaseServiceRequest[TestResponse], some_attr=True):
                                                                    ^^^^^^^^^^^^^^
            
            не передаются дальше в BaseServiceRequest.__init_subclass__.
            
            При втором вызове BaseServiceRequest.__init_subclass__ значение атрибута __mro__ выглядит так:

            >>> (
            >>>    <class '__main__.TestRequest'>,
            >>>    <class 'services.base.models.requests.BaseServiceRequest[TestResponse]'>,
            >>>    <class 'services.base.models.requests.BaseServiceRequest'>,
            >>>    ...
            >>> )

            и при этом ключевые аргументы, переданные при наследовании, передаются дальше
            в BaseServiceRequest.__init_subclass__.

            В связи с этой ситуации первый вызов метода BaseServiceRequest.__init_subclass__
            пропускается для обработки переданных при наследовании ключевых аргументов класса.
            """
            
            return
        
        unspecified_attrs = []

        for class_var_name in cls.__class_vars__:
            if class_var_name in ['_response_class', '_error_response_class']:
                class_var_value = None

                for base in cls.__mro__:
                    if not issubclass(base, BaseModel) or not hasattr(base, '__pydantic_generic_metadata__'):
                        continue

                    base_generic_args = base.__pydantic_generic_metadata__.get('args', ())

                    for base_generic_arg in base_generic_args:
                        match class_var_name:
                            case '_response_class':
                                if issubclass(base_generic_arg, ResponseType.__bound__ or type(None)):
                                    class_var_value = base_generic_arg
                            
                            case '_error_response_class':
                                if issubclass(base_generic_arg, ErrorResponseType.__bound__ or type(None)):
                                    class_var_value = base_generic_arg
                    
                    if class_var_value is not None:
                        break
            else:
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
