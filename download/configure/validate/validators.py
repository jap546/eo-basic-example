from typing import Any

import validators

from download.configure.validate import exceptions as e
from download.configure.validate import utils as u
from download.setup.constants import GEOMETRY_SERVERS


def validate_folder(folder: str) -> str:
    """Validation logic for a file folder.

    Requires a folder to not be empty and not contain any spaces.

    Arguments:
    ----------
    folder (str):
        folder value to be validated

    Returns:
    --------
    str: validated folder value
    """
    if u.empty_value(folder):
        msg = "File folder value must be populated"
        raise e.EmptyValError(msg)

    if u.string_contains_space(folder):
        msg = f"File folder value must not contain spaces. Folder: '{folder}'"
        raise e.InvalidSpaceError(msg)

    return folder


def validate_server(server: str) -> str:
    """Validation logic for a geospatial server.

    Requires a server to be a value from the GEOMETRY_SERVERS dictionary.

    Arguments:
    ----------
    server (str):
        server value to be validated

    Returns:
    --------
    str: validated server value
    """
    if server not in GEOMETRY_SERVERS:
        msg = f"Server must be in list of approved servers: {', '.join(GEOMETRY_SERVERS.keys())}"
        raise e.InvalidGeomServerError(msg)

    return server


def validate_output_filename(filename: str) -> str:
    """Validation logic for a filename.

    Requires a filename to not be empty, not contain any spaces,
    only contain a single underscore (_) and to have a valid year
    or year range.

    Required format [unique-filename_[year / year-range]

    Arguments:
    ----------
    filename (str):
        Filename value to be validated

    Returns:
    --------
    str: validated filename value
    """
    if u.empty_value(filename):
        msg = "Filenames must be populated"
        raise e.EmptyValError(msg)

    if u.string_contains_space(filename):
        msg = f"Filename must not contain spaces. Filename: '{filename}'"
        raise e.InvalidSpaceError(msg)

    if u.invalid_symbol_count(filename, "_", 1):
        msg = (
            "Filenames must contain a single underscore to separate the"
            " year value(s) at the end of the filename, e.g.,"
            f" 'filename-string_2019-2020'. Filename: '{filename}'"
        )
        raise e.InvalidNumberOfSymbolsError(msg)

    if not u.string_contains_year(filename):
        msg = (
            "Filename must contain a valid year after the underscore."
            " A valid year is either a 4 digit integer between 1990 and the"
            " current year or a hyphen separated range of years (e.g., 1990-2024)."
            f" Filename: '{filename}'"
        )
        raise e.InvalidYearError(msg)
    return filename


def validate_url(url: str) -> str:
    """Validation logic for a url.

    Utilises the validator library to check that url
    value is valid.

    Arguments:
    ----------
    url (str):
        URL value to be validated

    Returns:
    --------
    str: validated URL value
    """
    valid = validators.url(url)
    if not valid:
        msg = f"Given URL: '{url}' is not valid. Error: '{valid}'."
        raise e.InvalidValueFormatOrContentError(msg)
    return url


def validate_file_ext(ext: str) -> str:
    """Validation logic for file extensions.

    Checks that the value is not empty

    Arguments:
    ----------
    ext (str):
        File extension value to be validated

    Returns:
    --------
    str: validated file extension
    """
    if u.empty_value(ext):
        msg = "File extensions must be populated"
        raise e.EmptyValError(msg)
    return ext


def validate_filename(filename: str) -> str:
    """Validation logic for filenames.

    Checks that the filename is not empty

    Arguments:
    ----------
    filename (str):
        Filename value to be validated

    Returns:
    --------
    str: validated filename
    """
    if u.empty_value(filename):
        msg = "Filenames must be populated"
        raise e.EmptyValError(msg)

    return filename


def validate_api_strings(strings: list[str], title: str) -> None:
    """Validation logic for generic strings.

    Checks that each string is not empty and has no spaces. Raises
    an exception if any of them are invalid.

    Does not return a value as this is used in a model validator
    which returns the entire class, therefore indiviudual values
    are not required to be returned.

    Arguments:
    ----------
    strings (list[str]):
        String values to be validated

    title (str):
        Title of the file object, to be recorded in the log

    Returns:
    --------
        None
    """
    for string in strings:
        if u.empty_value(string):
            msg = (
                "Values provided for API parameters can no be empty. No value provided"
            )
            f" for a parameter for file: {title}."
            raise e.EmptyValError(msg)

        if u.string_contains_space(string):
            msg = "Parameter values can not contain spaces. Invalid parameter for file:"
            f" '{title}'."
            raise e.InvalidSpaceError(msg)


def validate_api_params(api_params: dict[str, Any]) -> dict[str, Any]:
    """Validation logic for api_params.

    Checks that the dictionary is not empty and that  no value is an empty
    string, on the assumption that if the key is defined, then the user
    intended to provide a value

    Arguments:
    ----------
    api_params (dict[str, Any]):
        api_params dictionary to be validated

    Returns:
    --------
    dict[str, Any]: validated api_params dictionary
    """
    if not api_params.keys():
        msg = "api_params dictionary must have at least one entry"
        raise e.EmptyValError(msg)

    for key, value in api_params.items():
        if u.empty_value(value):
            msg = f"API value for key {key} must be populated"
            raise e.EmptyValError(msg)

    return api_params


def validate_offset(offset: int, maximum: int) -> int:
    """Validation logic for offsets.

    Checks that the offset is not negative, or above the
    maximum threshold.

    Arguments:
    ----------
    offset (int):
        offset value to be validated

    maximum (int):
        Maximum offset allowed, based on the max records the API can return

    Returns:
    --------
    int: validated offset
    """
    if offset < 0:
        msg = "offsets must be a positive number"
        raise e.InvalidValueFormatOrContentError(msg)

    if offset > maximum:
        msg = "offset can not be greater than the provided maximum"
        raise e.InvalidValueFormatOrContentError(msg)

    return offset
