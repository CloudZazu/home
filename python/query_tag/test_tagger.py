import pytest

from .query_tag import Tagger

@pytest.fixture
def tagger():
    yield Tagger()

def get_scan_result_len(tagger: Tagger, line: str):
    tagger.scan(line, 1)
    return len(tagger.tags)

def test_spaces(tagger):
    assert get_scan_result_len(tagger, '   ') == 0

def test_valid_input(tagger):
    name = 'moooo'
    test_string = f'/*{name}*/'
    assert get_scan_result_len(tagger, test_string) == 1
    tag = tagger.tags[0]
    assert tag.name == name
    assert tag.start == 0
    assert tag.end == len(test_string)
    assert tag.match.string == test_string

def test_valid_input_with_symbols_in_nested_expression(tagger):
    name = 'mo/*#$#~*/ooo'
    test_string = f'/*{name}*/'
    assert get_scan_result_len(tagger, test_string) == 1
    tag = tagger.tags[0]
    assert tag.name == name
    assert tag.start == 0
    assert tag.end == len(test_string)
    assert tag.match.string == test_string

def test_valid_input_with_symbols(tagger):
    name = '$_$'
    capture_area = f'/*{name}*/'
    test_string = f'-_- ^_^ :) ;) {capture_area}ooo\\^_^/'
    assert get_scan_result_len(tagger, test_string) == 1
    tag = tagger.tags[0]
    assert tag.name == name
    assert tag.start == 14
    assert tag.end == tag.start + len(capture_area)
    assert tag.match.string == test_string
