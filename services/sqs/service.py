import boto3

from typing import Unpack

from loguru import logger

from services.base import BaseService

from .client import SQSAuthCredentials
from .models.entities import Message
from .exceptions import SQSConnectionException, SQSReceiveMessagesException, SQSDeleteMessageException


class SQSService(BaseService):
    """
    Сервис для работы с `AWS SQS`
    """
    
    
    def __init__(self, **auth_credentials: Unpack[SQSAuthCredentials]) -> None:
        self._auth_credentials = auth_credentials
    
    async def start(self) -> None:
        try:
            self._sqs_client = boto3.client(
                service_name='sqs',
                region_name=self._auth_credentials['region'],
                endpoint_url=self._auth_credentials['host'],
                aws_access_key_id=self._auth_credentials['access_key_id'].get_secret_value(),
                aws_secret_access_key=self._auth_credentials['secret_access_key'].get_secret_value()
            )
        except Exception as e:
            raise SQSConnectionException(str(e))
    
    def receive_messages(self) -> list[Message]:
        logger.info(f'{self.__class__.__name__}: Получение сообщений из очереди {self._auth_credentials['queue_name']}...')
        
        try:
            receive_message_response = self._sqs_client.receive_message(
                QueueUrl=self._auth_credentials['queue_url'],
                MessageSystemAttributeNames=['All'],
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )
        except Exception as e:
            logger.error((
                f'{self.__class__.__name__}: Не удалось получить сообщения из очереди {self._auth_credentials['queue_name']}, '
                f'возникло исключение {e.__class__.__name__}({e}).'
            ))
            
            raise SQSReceiveMessagesException(str(e))
        else:
            if len(receive_message_response.get('Messages', [])) == 0:
                logger.info(f'{self.__class__.__name__}: Новых сообщений в очереди {self._auth_credentials['queue_name']} не найдено.')
            else:
                logger.info(f'{self.__class__.__name__}: Сообщения ({len(receive_message_response.get('Messages', []))}) из очереди {self._auth_credentials['queue_name']} успешно получены.')
            
            return [Message(**raw_message) for raw_message in receive_message_response.get('Messages', [])] # pyright: ignore[reportCallIssue]


    def delete_message(self, message: Message) -> None:
        logger.info(f'{self.__class__.__name__}: Удаление сообщения {message.id} из очереди {self._auth_credentials['queue_name']}...')
        
        if message.receipt_handle is None:
            logger.warning((
                f'{self.__class__.__name__}: Не удалось удалить сообщение {message.id} из очереди {self._auth_credentials['queue_name']}, '
                'поскольку у сообщения отсутствует идентификатор получения сообщения (ReceiptHandle).'
            ))
            
            return
        
        try:
            self._sqs_client.delete_message(
                QueueUrl=self._auth_credentials['queue_url'],
                ReceiptHandle=message.receipt_handle
            )
        except Exception as e:
            logger.error((
                f'{self.__class__.__name__}: Не удалось удалить сообщение {message.id} из очереди {self._auth_credentials['queue_name']}, '
                f'возникло исключение {e.__class__.__name__}({e}).'
            ))

            raise SQSDeleteMessageException(str(e))
        else:
            logger.info(f'{self.__class__.__name__}: Сообщение {message.id} успешно удалено из очереди {self._auth_credentials['queue_name']}.')

    async def exit(self) -> None:
        if hasattr(self, '_sqs_client'):
            self._sqs_client.close()
