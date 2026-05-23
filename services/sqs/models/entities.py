from abc import ABC
from typing import Optional

from pydantic import Field

from services.base.models.entities import BaseServiceEntity

from ..types import MessageID
from ..enums import MessageSystemAttributeName


class BaseSQSEntity(BaseServiceEntity, ABC):
    pass


class MessageAttribute(BaseSQSEntity):
    data_type: str = Field(validation_alias='DataType')
    string_value: Optional[str] = Field(default=None, validation_alias='StringValue')
    binary_value: Optional[bytes] = Field(default=None, validation_alias='BinaryValue')
    string_list_values: Optional[list[str]] = Field(default=None, validation_alias='StringListValues')
    binary_list_values: Optional[list[bytes]] = Field(default=None, validation_alias='BinaryListValues')


class Message(BaseSQSEntity):
    """
    Модель сообщения `AWS SQS`
    """
    
    id: Optional[MessageID] = Field(default=None, validation_alias='MessageId')
    receipt_handle: Optional[str] = Field(default=None, validation_alias='ReceiptHandle')
    md5_of_body: Optional[str] = Field(default=None, validation_alias='MD5OfBody')
    body: Optional[str] = Field(default=None, validation_alias='Body')
    attributes: Optional[dict[MessageSystemAttributeName, str]] = Field(default=None, validation_alias='Attributes')
    md5_of_message_attributes: Optional[str] = Field(default=None, validation_alias='MD5OfMessageAttributes')
    message_attributes: Optional[dict[str, MessageAttribute]] = Field(default=None, validation_alias='MessageAttributes')
