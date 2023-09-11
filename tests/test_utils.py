import pytest

from webscraper.utils import flatten


def test_flatten():
    input_list = [[1, 2, 3], [4, 5], [6, 7, 8]]
    expected_output = [1, 2, 3, 4, 5, 6, 7, 8]
    assert flatten(input_list) == expected_output

    input_list = [[1, 2], [], [3, 4]]
    expected_output = [1, 2, 3, 4]
    assert flatten(input_list) == expected_output

    input_list = [1, 2, 3, 4, 5]
    with pytest.raises(ValueError):
        flatten(input_list)

    # Test case 5: empty list
    assert flatten([]) == []
