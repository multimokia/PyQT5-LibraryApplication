from library_connectors import Book
from typing import Any

class Session:
    def __init__(self):
        """
        Blank init function. This class can accept any property and value.
        """
        ...

    def __setattr__(self, __name: str, __value: Any) -> None:
        self.__dict__[__name] = __value
