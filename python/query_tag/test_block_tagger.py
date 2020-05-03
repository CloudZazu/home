import pytest

from .query_tag import Tagger, BlockTagger

name = 'THE ONE AND ONLY '

block_begin_text = f"""
i have no idea what i am doing
maybe i do
maybe i'll just tetris
/*<{name}>*/
"""

full_text = f"""
i have no idea what i am doing
maybe i do
maybe i'll just tetris
/*<{name}>*/
blah #$#$#$ --
/*<{name}/>*/
"""

# Adds invalid blockEnd syntax
invalid_block_end_full_text = f"""
i have no idea what i am doing
maybe i do
maybe i'll just tetris
/*<{name}>*/
blah #$#$#$ --
/*<{name}>*/
"""

@pytest.fixture
def tagger():
    yield Tagger()

@pytest.fixture
def block_tagger():
    yield BlockTagger()

def test_scan_block_begin(block_tagger):
    content = block_begin_text.split('\n')
    for line_num, line in enumerate(content):
        block_tagger.scan(line, line_num)

    assert len(block_tagger.tags) == 1
    assert block_tagger.tags[0].name == name

def test_scan_tags_block_begin(tagger, block_tagger):
    content = block_begin_text.split('\n')
    for line_num, line in enumerate(content):
        tagger.scan(line, line_num)

    block_tagger.scan_tags(tagger.tags)
    assert len(block_tagger.tags) == 1
    assert block_tagger.tags[0].name == name
    # Fails due to missing block ending syntax
    with pytest.raises(Exception):
        block_tags = block_tagger.get_blocks()

def test_scan_tags_invalid_block_end(tagger, block_tagger):
    content = invalid_block_end_full_text.split('\n')
    for line_num, line in enumerate(content):
        tagger.scan(line, line_num)

    block_tagger.scan_tags(tagger.tags)
    assert len(block_tagger.tags) == 2
    for tag in block_tagger.tags:
        assert tag.name == name

    # Fails due to missing block ending syntax
    with pytest.raises(Exception):
        block_tags = block_tagger.get_blocks()

def test_scan_tags_full_text(tagger, block_tagger):
    content = full_text.split('\n')
    for line_num, line in enumerate(content):
        tagger.scan(line, line_num)

    block_tagger.scan_tags(tagger.tags)
    assert len(block_tagger.tags) == 2
    for tag in block_tagger.tags:
        assert tag.name == name
    block_tags = block_tagger.get_blocks()
    assert len(block_tags) == 1
