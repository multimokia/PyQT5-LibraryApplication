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

    def __getattr__(self, attr: str) -> Any:
        return self.__dict__.get(attr)
