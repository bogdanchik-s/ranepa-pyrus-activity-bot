from services.base import BaseServiceException


class SQSException(BaseServiceException):
    pass


class SQSConnectionException(SQSException):
    pass


class SQSReceiveMessagesException(SQSException):
    pass


class SQSDeleteMessageException(SQSException):
    pass
