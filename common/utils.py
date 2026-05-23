import re


def camel_to_snake(camel_string: str) -> str:
    """
    Конвертирует строку из CamelCase в snake_case

    Args:
        camel_string (str): Строка в CamelCase для конвертации в snake_case
    
    Returns:
        Сконвертированная строка в snake_case
    """

    snake_string = re.sub(r'([A-Z]+)([A-Z][a-z])', lambda m: f'{m.group(1)}_{m.group(2)}', camel_string)
    snake_string = re.sub(r'([a-z])([A-Z])', lambda m: f'{m.group(1)}_{m.group(2)}', snake_string)
    snake_string = re.sub(r'([0-9])([A-Z])', lambda m: f'{m.group(1)}_{m.group(2)}', snake_string)
    snake_string = re.sub(r'([a-z])([0-9])', lambda m: f'{m.group(1)}_{m.group(2)}', snake_string)
    
    return snake_string.lower()
