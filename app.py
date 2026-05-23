import asyncio

from loguru import logger

from core import AppProcessManager
from services import DatabaseService, SQSService
from settings import AppSettings


class App:
    def __init__(self):
        logger.info('Инициализация приложения...')
        
        self.settings = AppSettings()

        self._database = DatabaseService(
            host=self.settings.database.host,
            port=self.settings.database.port,
            user=self.settings.database.user,
            password=self.settings.database.password,
            name=self.settings.database.name
        )

        self._sqs = SQSService(
            host=self.settings.sqs.host,
            region=self.settings.sqs.region,
            queue_name=self.settings.sqs.queue_name,
            queue_url=self.settings.sqs.queue_url,
            access_key_id=self.settings.sqs.access_key_id,
            secret_access_key=self.settings.sqs.secret_access_key
        )

        self._core = AppProcessManager(
            database=self._database,
            sqs=self._sqs
        )

        logger.info('Инициализация приложения завершена.')

    async def start(self) -> None:
        try:            
            logger.info('Запуск сервисов...')

            try:
                try:
                    await self._database.start()
                except Exception as e:
                    raise e
                else:
                    logger.info(f'{DatabaseService.__name__} успешно запущен.')

                try:
                    await self._sqs.start()
                except Exception as e:
                    raise e
                else:
                    logger.info(f'{SQSService.__name__} успешно запущен.')
            except Exception as e:
                logger.opt(exception=e).critical(f'Не удалось запустить сервисы, возникло исключение {e.__class__.__name__}.\n')
            else:
                logger.info('Сервисы успешно запущены.')

                await self._core.start_polling(interval=self.settings.events_polling_interval)
        except Exception as e:
            if not isinstance(e, (KeyboardInterrupt, SystemExit)):
                logger.opt(exception=e).critical(f'В процессе работы приложения возникло необработанное искоючение: {e.__class__.__name__}.\n')
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        logger.info('Завершение работы приложения...')

        try:
            logger.info('Остановка сервисов...')

            try:
                await self._database.exit()
            except Exception as e:
                logger.opt(exception=e).error(f'Не удалось корректно остановить работу {DatabaseService.__name__}, возникло иключение {e.__class__.__name__}.\n')

            try:
                await self._sqs.exit()
            except Exception as e:
                logger.opt(exception=e).error(f'Не удалось корректно остановить работу {SQSService.__name__}, возникло иключение {e.__class__.__name__}.\n')
        except:
            pass
        else:
            logger.info('Сервисы успешно остановлены.')

        try:
            logger.info('Сохранение настроек...')
            self.settings.save()
        except Exception as e:
            logger.opt(exception=e).error(f'Не удалось сохранить настройки, возникло исключение {e.__class__.__name__}.\n')
        else:
            logger.info('Настройки успешно сохранены.')

        logger.info('Приложение завершило работу.')

if __name__ == '__main__':
    app = App()
    asyncio.run(app.start())
