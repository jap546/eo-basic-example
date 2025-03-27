import datetime
from typing import Union


def empty_value(val: Union[str, int, list[str], None]) -> bool:
    """Checks if a value is empty.

    Checks if a value is None, consists of space, or is 0.

    Arguments:
    ----------
    val (Union[str, int, list[str], None]):
        Value to be checked

    Returns:
    --------
    bool: Whether the value is empty
    """
    if val is None:
        return True
    if isinstance(val, list):
        return val == [] or any((str(x).isspace() or len(x) == 0) for x in val)
    str_val = str(val)
    return str_val.isspace() or len(str_val) == 0


def validate_year(year: Union[int, str]) -> bool:
    """Checks if a year is valid.

    Checks whether a year is a valid integer and is between
    1990 and the current year

    Arguments:
    ----------
    year (Union[int, str]):
        Year to be checked

    Returns:
    --------
    bool: Whether the year is valid
    """
    curr_year = datetime.date.today().year

    try:
        int_year = int(year)
    except Exception:  # noqa: BLE001
        return False

    return 1990 <= int_year <= curr_year


def string_contains_year(string: str) -> bool:
    """Checks if a string contains a year, and if that year is valid.

    Extracts the value after the underscore (_), where the year value
    is expected to appear. Then validates each year value (either one, or
    two) depending on whether it is a year range

    Arguments:
    ----------
    string (str):
        string to be checked

    Returns:
    --------
    bool: Whether the string contains a valid year
    """
    # A config string containing years should have it after the only _ in the string
    year_values = string.split("_")[1]

    return all(validate_year(year) for year in year_values.split("-"))


def string_contains_space(string: str) -> bool:
    """Checks if a string contains any spaces.

    Arguments:
    ----------
    string (str):
        String to be checked

    Returns:
    --------
    bool: Whether the string contains a space
    """
    return len(string) > len(string.replace(" ", ""))


def invalid_symbol_count(string: str, symbol: str, occurences: int) -> bool:
    """Checks if a string contains more than the expected occurences of a symbol.

    Arguments:
    ----------
    string (str):
        String to be checked

    symbol (str):
        Symbol to be searched for

    occurences (int):
        Number of occurences of symbol expected

    Returns:
    --------
    bool: Whether the string contains a space
    """
    return len(string.split(symbol)) != occurences + 1
