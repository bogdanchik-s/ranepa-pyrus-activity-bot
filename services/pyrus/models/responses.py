from abc import ABC
from typing import Optional
from pydantic import SecretStr, AnyUrl, model_validator
from services.base.models.responses import BaseServiceResponse, BaseServiceFileResponse, BaseServiceErrorResponse
from .enums import PyrusResponseErrorCode
from .entities import AnyTask, RegistoryFormTask, Person, Profile, Form
from ..types import FormID


class BasePyrusResponse(BaseServiceResponse, ABC):
    pass


class BasePyrusFileResponse(BasePyrusResponse, BaseServiceFileResponse, ABC):
    pass


class BasePyrusErrorResponse(BaseServiceErrorResponse, ABC):
    error_code: Optional[PyrusResponseErrorCode] = None
    error: Optional[str] = None


class GetAccessTokenResponse(BasePyrusResponse):
    access_token: SecretStr
    api_url: Optional[AnyUrl] = None
    files_url: Optional[AnyUrl] = None


class GetProfileResponse(BasePyrusResponse):
    profile: Profile

    @model_validator(mode='before')
    @classmethod
    def model_validator(cls, input_data) -> dict:
        return {'profile': input_data}


class GetTaskResponse(BasePyrusResponse):
    task: AnyTask


class CommentTaskResponse(BasePyrusResponse):
    pass


class GetFormsResponse(BasePyrusResponse):
    forms: list[Form]

    @property
    def forms_dict(self) -> dict[FormID, Form]:
        return {f.id: f for f in self.forms}


class FormRegisterResponse(BasePyrusResponse):
    tasks: Optional[list[RegistoryFormTask]] = None


class GetFileResponse(BasePyrusFileResponse):
    pass


class GetPersonResponse(BasePyrusResponse):
    person: Person

    @model_validator(mode='before')
    @classmethod
    def model_validator(cls, input_data) -> dict:
        return {'person': input_data}
