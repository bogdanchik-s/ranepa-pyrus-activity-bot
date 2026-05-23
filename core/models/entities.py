from typing import Optional, Union
from pydantic import BaseModel, Field
from services.pyrus.models.entities import SimpleTaskComment, FormTaskComment


class PyrusTaskEventInfo(BaseModel):
    task_id: int = Field(validation_alias='taskId')
    form_id: Optional[int] = Field(default=None, validation_alias='formId')
    form_name: Optional[str] = Field(default=None, validation_alias='formName')
    comment: Union[FormTaskComment, SimpleTaskComment]
