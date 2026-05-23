import os
from functools import cached_property
from typing import TypeAlias
from pydantic import BaseModel, NonNegativeInt


Minutes: TypeAlias = NonNegativeInt
Seconds: TypeAlias = NonNegativeInt


class File(BaseModel):
    """
    Файл в байтах
    """

    mimetype: str
    content: bytes

    @cached_property
    def extension(self) -> str:
        import mimetypes
        return mimetypes.guess_extension(self.mimetype) or ''

    def save(self, filename: str, path: str) -> None:
        """Метод для локального сохранения файла

        Args:
            path (LiteralString): Путь до папки, в которую необходимо сохранить файл
            filename (LiteralString): Имя файла без его расширения (оно определяется автоматически)
        """
        
        os.makedirs(path, exist_ok=True)

        with open(os.path.join(path, filename + self.extension), mode='wb') as file:
            file.write(self.content)
