from abc import ABC
from http import HTTPMethod
from typing import Optional, Literal
from datetime import date
from aiohttp import ClientHandlerType, ClientRequest, ClientResponse
from yarl import URL
from pydantic import SecretStr, NonNegativeInt, PositiveInt, Field, field_serializer
from services.base import BaseServiceRequest

from ..types import TaskID, FormID, FormFieldIdentifier, PersonID
from .entities import FormFilter, BaseFormTaskComment
from .responses import (
    BasePyrusResponse,
    GetProfileResponse,
    GetFileResponse,
    BasePyrusErrorResponse,
    GetAccessTokenResponse,
    GetTaskResponse,
    CommentTaskResponse,
    GetFormsResponse,
    FormRegisterResponse,
    GetFileResponse,
    GetPersonResponse
)


class BasePyrusRequest[
    PyrusResponseType: BasePyrusResponse,
    PyrusErrorResponseType: BasePyrusErrorResponse
](BaseServiceRequest[PyrusResponseType, PyrusErrorResponseType], ABC):
    base_url = URL('https://api.pyrus.com/v4')

 
class GetAccessTokenRequest(BasePyrusRequest[GetAccessTokenResponse, BasePyrusErrorResponse], http_method=HTTPMethod.POST, endpoint=URL('/auth')):    
    base_url = URL('https://accounts.pyrus.com/api/v4')
    
    login: str
    person_id: Optional[NonNegativeInt] = None
    security_key: SecretStr


class GetProfileRequest(
    BasePyrusRequest[GetProfileResponse, BasePyrusErrorResponse],
    http_method=HTTPMethod.GET, endpoint=URL('/profile')
):
    pass


class GetTaskRequest(
    BasePyrusRequest[GetTaskResponse, BasePyrusErrorResponse],
    http_method=HTTPMethod.GET, endpoint=URL('/tasks/{task_id}')
):
    task_id: int = Field(exclude=True)


class CommentTaskRequest(
    BasePyrusRequest[CommentTaskResponse, BasePyrusErrorResponse], BaseFormTaskComment,
    http_method=HTTPMethod.POST, endpoint=URL('/tasks/{task_id}/comments')
):
    task_id: int = Field(exclude=True)

    skip_notification: Optional[bool] = None


class GetFormsRequest(
    BasePyrusRequest[GetFormsResponse, BasePyrusErrorResponse],
    http_method=HTTPMethod.GET, endpoint=URL('/forms')   
):
    pass


class FormRegisterRequest(
    BasePyrusRequest[FormRegisterResponse, BasePyrusErrorResponse],
    http_method=HTTPMethod.GET, endpoint=URL('/forms/{form_id}/register')
):
    form_id: FormID = Field(exclude=True)

    steps: Optional[list[NonNegativeInt]] = None
    include_archived: Optional[Literal['y']] = None
    modified_before: Optional[date] = None
    modified_after: Optional[date] = None
    created_before: Optional[date] = None
    created_after: Optional[date] = None
    closed_before: Optional[date] = None
    closed_after: Optional[date] = None
    filters: Optional[list[FormFilter]] = None
    format: Optional[Literal['csv']] = None
    delimiter: Optional[str] = None;
    simple_format: Optional[bool] = None
    encoding: Optional[str] = None
    field_identifiers: Optional[list[FormFieldIdentifier]] = Field(default=None, serialization_alias='field_ids')
    task_ids: Optional[list[TaskID]] = None
    # due_filter: Optional[DueFilter] = None
    item_count: Optional[PositiveInt] = None

    @field_serializer('field_identifiers', when_used='json', return_type=str)
    def field_identifiers_serializer(self, value: list[FormFieldIdentifier]) -> str:        
        return ','.join([str(field_id) for field_id in value])

    async def middleware(self, client_request: ClientRequest, client_handler: ClientHandlerType) -> ClientResponse:
        data = self.model_dump(mode='json', exclude={'filters'}, exclude_none=True)
        
        for form_filter in self.filters or []:
            data[f'fld{form_filter.field_identifier}'] = form_filter.filter_value

        client_request.url = client_request.url.update_query(**data)

        return await client_handler(client_request)


class GetFileRequest(
    BasePyrusRequest[GetFileResponse, BasePyrusErrorResponse],
    http_method=HTTPMethod.GET, endpoint=URL('/files/download/{file_id}')
):
    file_id: NonNegativeInt


class GetPersonRequest(
    BasePyrusRequest[GetPersonResponse, BasePyrusErrorResponse],
    http_method=HTTPMethod.GET, endpoint=URL('/members/{id}')
):
    id: PersonID
