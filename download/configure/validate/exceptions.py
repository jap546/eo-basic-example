class EmptyValError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class InvalidSpaceError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class InvalidNumberOfSymbolsError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class InvalidYearError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class MismatchYearsError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class DuplicateKeysError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class MultipleFundingKeysError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class InvalidValueFormatOrContentError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class InvalidApiParamsError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class MissingKeyError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class InvalidKeyError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class InvalidDateError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class DuplicateDefinitionError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class NonMatchingValuesError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)


class NonMatchingTitleColumnError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)

class InvalidGeomServerError(Exception):
    def __init__(self, msg: str) -> None:  # pragma: no cover
        super().__init__(msg)