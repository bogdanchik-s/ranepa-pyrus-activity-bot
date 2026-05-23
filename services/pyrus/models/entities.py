from abc import ABC
from typing import Any, NewType, Optional, Union, Literal, TypeAlias, Self
from typing_extensions import Annotated
from datetime import date, datetime, time
from functools import cached_property
from pydantic import NonNegativeInt, AnyUrl, Field,field_serializer, SerializerFunctionWrapHandler, TypeAdapter
from services.base import BaseServiceEntity
from ..types import (
    PersonID,
    RoleID,
    BotID,
    OrganizationID,
    DepartmentID,
    CatalogID,
    CatalogItemID,
    MultipleChoiceItemID,
    TableRowID,
    FormFieldID,
    FormFieldCode,
    FormFieldIdentifier,
    AttachmentID,
    TaskCommentID,
    TaskID,
    FormID,
    FormPrintFormID
)
from .enums import PyrusApprovalChoice, PyrusTaskAction, PyrusChannelType


class BasePyrusEntity(BaseServiceEntity, ABC):
    pass


# --- Самостоятельные сущности --- #


class Person(BasePyrusEntity):
    """
    Универсальная модель, которая может быть пользователем,
    ролью или ботом. Может быть ответственным за задачу,
    наблюдателем, согласующим, автором комментария и так далее,
    в `Pyrus` нет разделения на сущности в вышеуказанных сценариях.
    """
    
    id: PersonID
    type: Literal['user', 'role', 'bot']
    first_name: str
    last_name: str
    native_first_name: Optional[str] = None
    native_last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None # Тип `EmailStr` не подошел
    mobile_phone: Optional[str] = None
    status: Optional[str] = None
    position: Optional[str] = None
    locale: Optional[str] = None
    fired: Optional[bool] = None
    banned: Optional[bool] = None
    task_receiver: Optional[PersonID] = None
    department_id: Optional[DepartmentID] = None
    department_name: Optional[str] = None


class Role(BasePyrusEntity):
    id: RoleID
    name: Optional[str] = None
    fired: Optional[bool] = None
    banned: Optional[bool] = None
    member_ids: Optional[list[PersonID]] = None
    type: Literal['role']


class Bot(BasePyrusEntity):
    id: BotID
    name: Optional[str] = None
    is_enabled: Optional[bool] = None
    fired: Optional[bool] = None
    hook_url: Optional[AnyUrl] = None
    description: Optional[str] = None
    bot_settings: Optional[dict] = None
    login: Optional[str] = None # Есть боты без логина (встроенные)
    send_only_last_comment: Optional[bool] = None
    locale: Optional[str] = None
    time_zone_offset: Optional[NonNegativeInt] = None
    type: Literal['bot']


class Organization(BasePyrusEntity):
    id: OrganizationID
    name: str
    persons: list[Person]
    roles: list[Role]
    department_catalog_id: CatalogID


class Profile(BasePyrusEntity):
    person_id: PersonID
    first_name: str
    last_name: str
    email: str # Тип `EmailStr` не подошел
    locale: str
    organization_id: OrganizationID
    organization: Organization


class ChannelMember(BasePyrusEntity):
    email: Optional[str] = None # Тип `EmailStr` не подошел
    name: Optional[str] = None

    @property
    def email_or_name(self) -> str | None:
        return self.email or self.name


class Channel(BasePyrusEntity):
    type: PyrusChannelType
    recipient: ChannelMember = Field(alias='to')
    sender: ChannelMember = Field(alias='from')


# --- ### --- #


# --- Сущности, непосредственно относящиеся к задачам --- #


class Attachment(BasePyrusEntity):
    id: AttachmentID
    name: str
    size: NonNegativeInt
    md5: str
    url: AnyUrl
    version: NonNegativeInt
    root_id: Optional[NonNegativeInt] = None


class BaseTaskComment(BasePyrusEntity, ABC):
    text: Optional[str] = None
    formatted_text: Optional[str] = None
    added_list_ids: Optional[list[NonNegativeInt]] = None
    removed_list_ids: Optional[list[NonNegativeInt]] = None
    reassigned_to: Optional[Person] = None
    approval_choice: Optional[PyrusApprovalChoice] = None
    participants_added: Optional[list[Person]] = None
    participants_removed: Optional[list[Person]] = None
    subscribers_added: Optional[list[Person]] = None
    subscribers_removed: Optional[list[Person]] = None
    subscribers_rerequested: Optional[list[Person]] = None
    due_date: Optional[datetime] = None
    duration: Optional[NonNegativeInt] = None
    attachments: Optional[list[Attachment]] = None
    action: Optional[PyrusTaskAction] = None
    spent_minutes: Optional[NonNegativeInt] = None
    mentions: Optional[list[PersonID]] = None
    reply_note_id: Optional[TaskCommentID] = None
    comment_as_roles: Optional[list[Role]] = None
    channel: Optional[Channel] = None


class SimpleTaskComment(BaseTaskComment):
    id: TaskCommentID
    create_date: datetime
    author: Person


class BaseTask(BasePyrusEntity, ABC):
    """
    Модель базовой структуры задачи `Pyrus`,
    котоорая присуща всем типам задач
    """

    id: TaskID
    create_date: datetime
    last_modified_date: datetime
    due_date: Optional[date] = None
    due: Optional[datetime] = None
    duration: Optional[NonNegativeInt] = None
    close_date: Optional[datetime] = None
    current_step: NonNegativeInt
    list_ids: list[NonNegativeInt] = []
    attachments: list[Attachment] = []
    parent_task_id: Optional[TaskID] = None
    linked_task_ids: list[TaskID] = []


class SimpleTask(BaseTask):
    """
    Модель простой задачи (не по форме) в `Pyrus`
    """

    text: str
    author: Person
    responsible: Person
    participants: list[Person]
    comments: Optional[list[SimpleTaskComment]] = None


class Form(BasePyrusEntity):
    id: FormID
    name: str
    deleted_or_closed: bool
    folder: Optional[list[str]] = None
    steps: Optional[dict[str, str]] = None
    business_owners: Optional[list[PersonID]] = None
    fields: Optional[list['AnyFormField']] = None
    print_forms: Optional[list['FormPrintForm']] = None


class FormPrintForm(BasePyrusEntity):
    id: Optional[FormPrintFormID] = Field(default=None, validation_alias='print_form_id')
    name: str = Field(validation_alias='print_form_name')


class FormFilter(BasePyrusEntity):
    field_identifier: FormFieldIdentifier
    operator_id: Literal[
        'Equals',
        'GreaterThan',
        'IsEmpty',
        'IsIn',
        'LessThan',
        'Range'
    ]
    values: list[str]

    @property
    def filter_value(self) -> str:
        if len(self.values) == 0:
            return ''
        
        match self.operator_id:
            case 'Equals':
                return f'eq.{self.values[0]}'
        
            case 'GreaterThan':
                return f'gt{self.values[0]}'

            case 'IsEmpty':
                return 'empty'
            
            case 'IsIn':
                return ','.join(self.values)

            case 'LessThan':
                return f'lt{self.values[0]}'

            case 'Range':
                if len(self.values) < 2:
                    return ''
                
                return f'gt{self.values[0]},lt{self.values[1]}'

# --- Модели полей формы --- #


class BaseFormField(BasePyrusEntity, ABC):
    id: Optional[FormFieldID] = None
    code: Optional[FormFieldCode] = None
    type: Any
    name: Optional[str] = None
    tooltip: Optional[str] = None
    value: Optional[Any] = None
    info: Optional[dict] = None
    parent_id: Optional[FormFieldID] = None
    row_id: Optional[NonNegativeInt] = None


TextFormFieldValue: TypeAlias = str


class TextFormField(BaseFormField):
    type: Literal['text'] = 'text'
    value: Optional[TextFormFieldValue] = None


NumberFormFieldValue: TypeAlias = float


class NumberFormField(BaseFormField):
    type: Literal['number'] = 'number'
    value: Optional[NumberFormFieldValue] = None


MoneyFormFieldValue: TypeAlias = float


class MoneyFormField(BaseFormField):
    type: Literal['money'] = 'money'
    value: Optional[MoneyFormFieldValue] = None


DateFormFieldValue: TypeAlias = date


class DateFormField(BaseFormField):
    type: Literal['date'] = 'date'
    value: Optional[DateFormFieldValue] = None


TimeFormFieldValue: TypeAlias = time


class TimeFormField(BaseFormField):
    type: Literal['time'] = 'time'
    value: Optional[TimeFormFieldValue] = None

    @field_serializer('value')
    def value_serializer(self, value: time) -> str:
        return value.strftime('%H:%M')


CheckmarkFormFieldValue: TypeAlias = Literal['checked', 'unchecked']


class CheckmarkFormField(BaseFormField):
    type: Literal['checkmark'] = 'checkmark'
    value: Optional[CheckmarkFormFieldValue] = None

    def __bool__(self) -> bool:
        return self.value == 'checked'


EmailFormFieldValue: TypeAlias = str


class EmailFormField(BaseFormField):
    type: Literal['email'] = 'email'
    value: Optional[EmailFormFieldValue] = None # Тип `EmailStr` не подошел


PhoneFormFieldValue: TypeAlias = str


class PhoneFormField(BaseFormField):
    type: Literal['phone'] = 'phone'
    value: Optional[PhoneFormFieldValue] = None


PersonFormFieldValue: TypeAlias = Person


class PersonFormField(BaseFormField):
    type: Literal['person'] = 'person'
    value: Optional[PersonFormFieldValue] = None


class FormLinkFormFieldValue(BasePyrusEntity):
    task_ids: list[TaskID]
    subject: str


class FormLinkFormFieldValueWriter(BasePyrusEntity):
    task_ids: list[TaskID]


class FormLinkFormField(BaseFormField):
    type: Literal['form_link'] = 'form_link'
    value: Optional[FormLinkFormFieldValue] = None


AttachmentFormFieldValue: TypeAlias = list[Attachment]


class AttachmentFormField(BaseFormField):
    type: Literal['file'] = 'file'
    value: Optional[AttachmentFormFieldValue] = None


class CatalogFormFieldValue(BasePyrusEntity):
    item_id: Optional[CatalogItemID] = None
    item_ids: Optional[list[CatalogItemID]] = None
    item_name: Optional[str] = None
    item_names: Optional[list[str]] = None
    headers: Optional[list[str]] = None
    values: Optional[list[Any]] = None
    rows: Optional[list[list[Any]]] = None


class CatalogFormFieldValueWriter(BasePyrusEntity):
    item_id: Optional[CatalogItemID] = None
    item_ids: Optional[list[CatalogItemID]] = None
    item_name: Optional[str] = None
    item_names: Optional[list[str]] = None


class CatalogFormField(BaseFormField):
    type: Literal['catalog'] = 'catalog'
    value: Optional[CatalogFormFieldValue] = None


class MultipleChoiceFormFieldValue(BasePyrusEntity):
    choice_ids: list[MultipleChoiceItemID]
    choice_names: list[str]


class MultipleChoiceFormFieldValueWriter(BasePyrusEntity):
    choice_ids: list[MultipleChoiceItemID]


class MultipleChoiceFormField(BaseFormField):
    type: Literal['multiple_choice'] = 'multiple_choice'
    value: Optional[MultipleChoiceFormFieldValue] = None


_UserFieldValue = Union[
    TextFormFieldValue,
    NumberFormFieldValue,
    MoneyFormFieldValue,
    DateFormFieldValue,
    TimeFormFieldValue,
    PhoneFormFieldValue,
    EmailFormFieldValue,
    PersonFormFieldValue,
    AttachmentFormFieldValue,
    CheckmarkFormFieldValue,
    CatalogFormFieldValueWriter,
    MultipleChoiceFormFieldValueWriter,
    FormLinkFormFieldValueWriter
]


_UserField = Annotated[Union[
    TextFormField,
    NumberFormField,
    MoneyFormField,
    DateFormField,
    TimeFormField,
    PhoneFormField,
    EmailFormField,
    PersonFormField,
    AttachmentFormField,
    CheckmarkFormField,
    CatalogFormField,
    MultipleChoiceFormField,
    FormLinkFormField
], Field(discriminator='type')]


class AuthorFormField(BaseFormField):
    type: Literal['author'] = 'author'
    value: Optional[Person] = None


class PersonResponsibleField(BaseFormField):
    type: Literal['person_responsible'] = 'person_responsible'
    value: Optional[Person] = None


class StatusFormField(BaseFormField):
    type: Literal['status'] = 'status'
    value: Optional[Literal['open', 'closed']] = None


class StepFormField(BaseFormField):
    type: Literal['step'] = 'step'
    value: Optional[NonNegativeInt] = None


class FlagFormField(BaseFormField):
    type: Literal['flag'] = 'flag'
    value: Optional[Literal['none', 'checked', 'unchecked']] = None


class CreationDateFormField(BaseFormField):
    type: Literal['creation_date'] = 'creation_date'
    value: Optional[datetime] = None


class DueDateFormField(BaseFormField):
    type: Literal['due_date'] = 'due_date'
    value: Optional[date] = None
    duration: Optional[NonNegativeInt] = None


class DueDateTimeFormField(BaseFormField):
    type: Literal['due_date_time'] = 'due_date_time'
    value: Optional[datetime] =  None
    duration: Optional[NonNegativeInt] = None


_SystemField = Annotated[Union[
    AuthorFormField,
    PersonResponsibleField,
    StatusFormField,
    StepFormField,
    FlagFormField,
    CreationDateFormField,
    DueDateFormField,
    DueDateTimeFormField
], Field(discriminator='type')]


class NoteFormField(BaseFormField):
    type: Literal['note'] = 'note'
    value: Optional[str] = None


class TableFormFieldRowValueSetter(BasePyrusEntity):
    row_id: TableRowID
    position: Optional[NonNegativeInt] = None
    delete: Optional[bool] = None
    cells: list[_UserFieldValue]


class TableFormFieldRow(BasePyrusEntity):
    row_id: TableRowID
    position: Optional[NonNegativeInt] = None
    delete: Optional[bool] = None
    deleted: Optional[bool] = None
    cells: list[Annotated[_UserField, Field(discriminator='type')]] = []


TableFormFieldValueSetter: TypeAlias = list[TableFormFieldRowValueSetter]


class TableFormField(BaseFormField):
    type: Literal['table'] = 'table'
    value: Optional[list[TableFormFieldRow]] = None

    def get_cell(self, field_identifier: FormFieldIdentifier, row_id: TableRowID) -> _UserField | None:
        if self.value is None:
            return
        
        if len(self.value) < row_id:
            return 
        
        for cell in self.value[row_id].cells:
            if cell.id == field_identifier or cell.code == field_identifier:
                return cell


class TitleFormFieldValue(BasePyrusEntity):
    checkmark: Literal['checked', 'unchecked'] = 'unchecked'
    fields: list[Annotated[Union[_UserField, _SystemField, NoteFormField, TableFormField, 'TitleFormField'], Field(discriminator='type')]]


class TitleFormField(BaseFormField):
    type: Literal['title'] = 'title'
    value: Optional[TitleFormFieldValue] = None


_LayoutField = Annotated[Union[
    NoteFormField,
    TableFormField,
    TitleFormField
], Field(discriminator='type')]


AnyFormField = Annotated[Union[
    _UserField,
    _SystemField,
    _LayoutField
], Field(discriminator='type')]


class FormFieldValueWriter(BasePyrusEntity):
    id: Optional[FormFieldID] = None
    code: Optional[FormFieldCode] = None
    value: Union[_UserFieldValue, TableFormFieldValueSetter]
    row_id: Optional[TableRowID] = None

    @field_serializer('value', mode='wrap', when_used='json')
    def value_serializer(self, value: Union[_UserFieldValue, TableFormFieldValueSetter], serializer: SerializerFunctionWrapHandler) -> str:
        if isinstance(value, (datetime, date)):
            return value.strftime('%Y-%m-%d')
        
        if isinstance(value, time):
            return value.strftime('%H:%M')
        
        return serializer(value)


# --- ### --- #


class Approving(BasePyrusEntity):
    person: Person
    approval_choice: Optional[PyrusApprovalChoice] = None
    step: Optional[NonNegativeInt] = None


ApprovalStep = NewType('ApprovalStep', list[Approving])


class BaseFormTaskComment(BaseTaskComment):
    changed_step: Optional[NonNegativeInt] = None
    approvals_added: Optional[list[ApprovalStep]] = None
    approvals_removed: Optional[list[ApprovalStep]] = None
    approvals_rerequested: Optional[list[ApprovalStep]] = None
    field_updates: Optional[list[Annotated[Union[_UserField, _LayoutField], Field(discriminator='type')]]] = None


class FormTaskComment(BaseFormTaskComment):
    id: TaskCommentID
    create_date: datetime
    author: Person


TaskComment = TypeAdapter[Union[FormTaskComment, SimpleTaskComment]](Union[FormTaskComment, SimpleTaskComment])


class BaseFormTask(BaseTask, ABC):
    """
    Базовая модель задачи по форме в `Pyrus`
    """

    fields: list[AnyFormField]

    @cached_property
    def flat_fields(self) -> list[AnyFormField]:
        fields = []

        for field in self.fields or []:
            match field.type:
                case 'title':
                    if field.value is not None:
                        fields.extend(field.value.fields)
            
                case 'table':
                    for table_row in field.value or []:
                        if table_row.cells is not None:
                            fields.extend(table_row.cells)
                
                case _:
                    fields.append(field)

        return fields

    def get_flat_field(self, field_identifier: FormFieldIdentifier) -> AnyFormField | None:
        for field in self.fields or []:
            if field.id == field_identifier or field.code == field_identifier:
                return field

            if field.type == 'title' and field.value is not None:
                for nested_field in field.value.fields or []:
                    if nested_field.id == field_identifier or nested_field.code == field_identifier:
                        return nested_field


class FormTask(BaseFormTask):
    """
    Модель задачи по форме в `Pyrus`
    """

    form_id: FormID
    author: Person
    approvals: list[ApprovalStep]
    subscribers: list[Approving]
    comments: Optional[list[FormTaskComment]] = None


class RegistoryFormTask(BaseFormTask):
    """
    Модель задачи из реестра формы
    """


AnyTask = Union[SimpleTask, FormTask]

# --- ### --- #
