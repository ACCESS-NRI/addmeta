#!/usr/bin/env python

"""
Copyright 2025 ACCESS-NRI

author: Aidan Heerdegen <aidan.heerdegen@anu.edu.au>

Licensed under the Apache License, Version 2.0 (the "License"),
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import pytest

from addmeta import array_to_csv, serialise_dict_values

@pytest.mark.parametrize("array,string", 
    [ 
        (('a',1,'three four','five, six'), 'a,1,three four,"five, six"'),
        (['a',1,'three four','five, six'], ('a,1,three four,"five, six"')),
    ],
)
def test_array_to_csv(array, string):
    """
    Test function to convert arrays into comma separated strings
    """
    assert array_to_csv(array) == string

def test_array_to_csv_with_quoted_element():
    """
    Test that array_to_csv issues a warning when passed a double quoted element
    """
    array = ('"quoted"', 1)
    warning_text = 'Serialisation failed for .* no escapechar set'
    with pytest.warns(UserWarning, match=warning_text):
        result = array_to_csv(array)
    assert result == array

def test_serialise_dict_values():
    """
    Test for test_serialise_dict_values which serialises dictionary values
    """
    test_dict = { 1: [2, 3, 4], 5: 6, 7: [8, '9', '10']}
    serialised_dict = { 1: '2,3,4', 5: 6, 7: '8,9,10' }

    assert( serialise_dict_values(test_dict) == serialised_dict )
