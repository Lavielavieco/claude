"""Utility functions for the claude project."""


def flatten(nested_list):
    """Flatten a nested list into a single list.

    Args:
        nested_list: A list that may contain nested lists at any depth.

    Returns:
        A single flat list with all elements.

    Examples:
        >>> flatten([1, [2, 3], [4, [5, 6]]])
        [1, 2, 3, 4, 5, 6]
        >>> flatten([])
        []
        >>> flatten([1, 2, 3])
        [1, 2, 3]
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result


def chunk(lst, size):
    """Split a list into chunks of a given size.

    Args:
        lst: The list to split.
        size: The maximum size of each chunk.

    Returns:
        A list of lists, each with at most `size` elements.

    Examples:
        >>> chunk([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
        >>> chunk([], 3)
        []
    """
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def deep_merge(dict1, dict2):
    """Deep merge two dictionaries.

    Values in dict2 take precedence. Nested dicts are merged recursively
    rather than overwritten.

    Args:
        dict1: The base dictionary.
        dict2: The dictionary to merge in (takes precedence).

    Returns:
        A new merged dictionary.

    Examples:
        >>> deep_merge({"a": 1, "b": {"c": 2}}, {"b": {"d": 3}})
        {'a': 1, 'b': {'c': 2, 'd': 3}}
    """
    result = dict(dict1)
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
