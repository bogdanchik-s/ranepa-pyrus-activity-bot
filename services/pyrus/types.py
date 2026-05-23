from typing import TypeAlias, Union
from pydantic import NonNegativeInt


PersonID: TypeAlias = NonNegativeInt
RoleID: TypeAlias = NonNegativeInt
BotID: TypeAlias = NonNegativeInt
OrganizationID: TypeAlias = NonNegativeInt
DepartmentID: TypeAlias = NonNegativeInt
CatalogID: TypeAlias = NonNegativeInt
CatalogItemID: TypeAlias = NonNegativeInt
MultipleChoiceItemID: TypeAlias = NonNegativeInt
TableRowID: TypeAlias = NonNegativeInt
FormFieldID: TypeAlias = NonNegativeInt
FormFieldCode: TypeAlias = str
FormFieldIdentifier = Union[FormFieldID, FormFieldCode]
AttachmentID: TypeAlias = NonNegativeInt
TaskCommentID: TypeAlias = NonNegativeInt
TaskID: TypeAlias = NonNegativeInt
FormID: TypeAlias = NonNegativeInt
FormPrintFormID: TypeAlias = NonNegativeInt
