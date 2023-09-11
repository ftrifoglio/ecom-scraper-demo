"""Utilities functions."""

from typing import Any


def flatten(list_of_lists: list[list]) -> list[Any]:
    """Flatten a list of lists."""
    if not all(isinstance(sublist, list) for sublist in list_of_lists):
        raise ValueError("All elements of the input must be of type list.")
    return [item for sublist in list_of_lists for item in sublist]
