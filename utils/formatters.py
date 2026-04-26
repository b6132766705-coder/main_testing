def fmt(num: int) -> str:
    """Форматирует числа, добавляя пробелы (10000 -> 10 000)"""
    return f"{num:,}".replace(",", " ")
