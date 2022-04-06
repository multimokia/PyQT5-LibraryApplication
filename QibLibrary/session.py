"""
Module implements Session helper class
"""

# from library_connectors import Book
from typing import Any

class Session:
    """
    A helper class that can hold any attributes
    """
    def __init__(self):
        """
        Blank init function. This class can accept any property and value.
        """
        ...# pylint: disable=unnecessary-ellipsis

    def __setattr__(self, __name: str, __value: Any) -> None:
        self.__dict__[__name] = __value
