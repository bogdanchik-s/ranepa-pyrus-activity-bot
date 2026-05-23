from services.base import BaseServiceException


class DatabaseException(BaseServiceException):
    pass


class DatabaseSelectException(DatabaseException):
    pass


class DatabaseInsertException(DatabaseException):
    pass
