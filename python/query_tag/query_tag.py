import re

from collections import deque
from typing import List

class Tag:
    regex = r'\/\*(.*)\*\/'
    
    def __init__(self, string: str, line_num: int):
        if type(line_num) != int:
            raise Exception('Unsupported line_num type - Must be int type')

        match = self.scan(string)

        self.string = string
        self.line_num = line_num

        self.match = match
        self.name = match.group(1)

        # String start and end indexes
        self.start = match.start(0)
        self.end = match.end(0)

    @classmethod
    def scan(cls, line):
        return re.search(cls.regex, line)

class BlockTagBegin(Tag):
    regex = r'\/\*<(.*[^\/])>\*\/'
    
class BlockTagEnd(Tag):
    regex = r'\/\*<(.*)\/>\*\/'
    
class BlockTag:
    start_tag = BlockTagBegin
    end_tag = BlockTagEnd
    
    def __init__(self, start: Tag, end: Tag):
        if start.name != end.name:
            raise Exception('names not equal')
        
        self.start = start
        self.end = end
        
        self.name = self.start.name
        print('*'*100)
        print('start')
        print(self.start.__dict__)
        print('end')
        print(self.end.__dict__)
        
class Tagger:
    def __init__(self):
        self.tags = list()

    def scan(self, line, line_num):
        match = Tag.scan(line)
        if match:
            tag = Tag(line, line_num)
            self.tags.append(tag)


class BlockTagger(Tagger):
    def __init__(self):
        super(BlockTagger, self).__init__()
        self.block_tags = list()
        self.nonblock_tags = list()

    def scan(self, line, line_num):
        start_tag = BlockTag.start_tag
        start_match = start_tag.scan(line)
        if start_match:
            self.tags.append(BlockTagBegin(line, line_num))

        end_tag = BlockTag.end_tag
        end_match = end_tag.scan(line)
        if end_match:
            self.tags.append(BlockTagEnd(line, line_num))

        no_match = not (start_match or end_match)
        if no_match:
            self.nonblock_tags.append(line)

    def scan_tags(self, tags: List[Tag]):
        
        for tag in tags:
            start_tag = BlockTag.start_tag
            start_match = start_tag.scan(tag.match.string)
            if start_match:
                self.tags.append(BlockTagBegin(tag.string, tag.line_num))

            end_tag = BlockTag.end_tag
            end_match = end_tag.scan(tag.match.string)
            if end_match:
                self.tags.append(BlockTagEnd(tag.string, tag.line_num))

            no_match = not(start_match or end_match)
            if no_match:
                self.nonblock_tags.append(tag)
        
    def get_blocks(self):
        self.tags.sort(key=lambda item : (item.name, item.line_num))

        print([(item.name, item.line_num, item.start, item.end) for item in self.tags])
        prev_tag_name = None
        begin_tags = deque()
        end_tags = deque()
        
        for tag in self.tags:
            if prev_tag_name != tag.name:
                self._connect_current_tag_block(begin_tags, end_tags)
                    
            if type(tag) == BlockTagBegin:
                begin_tags.append(tag)  
            elif type(tag) == BlockTagEnd:
                end_tags.append(tag)
            else:
                raise Exception('incorrect type')
                
            prev_tag_name = tag.name   
            
        block_tags = self._connect_current_tag_block(begin_tags, end_tags)
        return block_tags
        
    def _connect_current_tag_block(self, begin_tags, end_tags):
        if len(begin_tags) != len(end_tags):
            if len(begin_tags) > len(end_tags):
                broken_tag = begin_tags[-1]
                raise Exception(f'Ending tag missing for {broken_tag.name} on line num: {broken_tag.line_num+1}')
            else:
                broken_tag = end_tags[-1]
                raise Exception(f'Beginning tag missing for {broken_tag.name} on line num: {broken_tag.line_num+1}')

        block_tags = list()
        for i in range(len(begin_tags)):
            start_tag = begin_tags.popleft()
            end_tag = end_tags.popleft()

            block_tag = BlockTag(start_tag, end_tag)
            print(f'Connect - Block_tag_name: {block_tag.name} - Line nums: {block_tag.start.line_num}:{block_tag.end.line_num}')
            block_tags.append(block_tag)
        return block_tags

class SqlFileTemplate:
    def __init__(self, content, query_tags, line_tags, block_tags):
        self.content = content
        self._query_tags = query_tags
        self._line_tags = line_tags
        self._block_tags = block_tags
        self._lines = None
    @property
    def query_tags(self):
        return get_interval_dict(tags=self._query_tags)

    @property
    def line_tags(self):
        return get_interval_dict(tags=self._line_tags)

    @property
    def block_tags(self):
        return get_interval_dict(block_tags=self._block_tags)

    def dump(self, abs_path, comment_mode=True):
        # Dump modes - local usable fashion and no comments
        if not self.content:
            raise Exception('No data found')


        if comment_mode:
            file_query_list = '\n'.join(self.content)
        else:
            file_query_list = self.to_list()

        with open(abs_path, 'w') as fp:
            fp.writelines(file_query_list)

    def to_list(self):
        lines = self.content
        valid_lines = [line for line in lines if line and not line.startswith('--')]
        file_query_str = '\n'.join(valid_lines)
        file_query_list = re.split(r'{}\s*\n'.format(';'), file_query_str)   # noqa W605
        return file_query_list

    def __repr__(self):
        return '\n'.join(self.content)

    def __iter__(self):
        # Iterates by query
        self._lines = self.to_list()
        self.n = -1
        self.max = len(self._lines)
        return self

    def __next__(self):
        self.n += 1
        if self.n < self.max:
            return self._lines[self.n]
        else:
            raise StopIteration

class SqlFileParser:
    def __init__(self, abs_filepath=None, log_handler=None):
        self.lines = None
        self._log = log_handler
        self.rendered_content = None
        if abs_filepath:
            self.lines = self.read_sql_file(abs_filepath)

    @property
    def log(self, msg=None):
        def empty_log(msg):
            pass

        if self._log:
            return self._log
        else:
            return empty_log

    def read_sql_file(self, fp):
        lines = list()
        with open(fp, 'r') as file:
            for line in file:
                lines.append(line.strip())
        return lines

    def run(self, content: str=None,
            run_tags: List[str]=None,
            exclude: List[str]=None):

        if content:
            self.lines = content.split('\n')

        if not self.lines:
            raise Exception('No lines loaded')

        delimited_line_region = self.lines

        IGNORE_SQL_COMMENTED_LINES = r'^[\s]*--'
        tagger = Tagger()
        for line_num, line in enumerate(delimited_line_region):
            if re.search(IGNORE_SQL_COMMENTED_LINES, line):
                continue

            self.log(f'Line num: {line_num} - Line: {line}')
            tagger.scan(line, line_num)
        self.log('\n')
        self.log(f'Tags:\n{tagger.tags}\n')

        block_tagger = BlockTagger()
        block_tagger.scan_tags(tagger.tags)
        self.log(f'Block signature tags(begin/end):\n{block_tagger.tags}\n')

        block_tags = block_tagger.get_blocks()
        self.log(f'Block tags (as a whole):\n{block_tags}\n')
        self.log(f'Non-block tags found after classifying:\n{block_tagger.nonblock_tags}\n')

        for block_tag in block_tags:
            self.log(f'Block_tag_name: {block_tag.name} - Line nums: {block_tag.start.line_num}:{block_tag.end.line_num}')

        line_tags, query_tags = get_line_tags(block_tagger.nonblock_tags)
        block_tag_linenum_dict = get_block_tag_overlap_ranges(block_tags)

        found_keys = get_tag_keys(line_tags, block_tags)

        # Interpret filtering scheme
        if not run_tags and exclude:
            # Selects All Available Tags - Exclude tags
            selected_tags = [name for name in found_keys if name not in exclude]
        elif run_tags and exclude:
            # Selects Run Tags - Exclude Tags
            selected_tags = [name for name in run_tags if name not in exclude]
        else:
            selected_tags = run_tags

        interval_dict = get_interval_dict(tags=line_tags, block_tags=block_tags)
        self.log(f'Interval Dict: {interval_dict}')
        check_for_interval_overlap(interval_dict)

        tags = list()
        tags.extend(line_tags)
        tags.extend(block_tags)

        render_code(selected_tags, tags, delimited_line_region)

        return SqlFileTemplate(delimited_line_region, query_tags=query_tags, line_tags=line_tags, block_tags=block_tags)


def get_line_tags(nonblock_tags):
    # Evaluate whether its a query tag or a line tag
    line_tags = list()
    query_tags = list()

    print('Checking whether its a query tag or line tag')
    for tag in nonblock_tags:
        if tag.start == 0:
            line_tags.append(tag)
            print(f'this is a line tag - {tag.name}')
        else:
            query_tags.append(tag)

        print(f'Line number: {tag.line_num} - Indexes: {tag.match.start()}:{tag.match.end()}')
    return line_tags, query_tags


def get_tag_keys(line_tags, block_tags):
    conditional_tags = list()
    conditional_tags.extend(line_tags)
    conditional_tags.extend(block_tags)

    keys = {tag.name for tag in conditional_tags}
    print(f'Found keys: {keys}\n')
    return keys


def render_code(run_tags, tags: List[Tag], delimited_line_region: List[str]):
    # ensure tags has only blocktags and linetags

    selected_keys = dict()

    if run_tags:
        for name in run_tags:
            selected_keys[name] = 0

    sql_comment_prefix = '--'

    line_num_deletion_list = list()

    for tag in tags:
        if type(tag) == BlockTag:
            remove_tag_list = [tag.start, tag.end]
        else:
            remove_tag_list = [tag]

        # Block tags - Remove tag and comment range if appropriate
        # Line tags - Remove tag and comment if appropriate
        for cur_tag in remove_tag_list:
            end_idx = cur_tag.end
            line_num = cur_tag.line_num

            print(f'{cur_tag.string[cur_tag.start:end_idx]} End_idx: {end_idx}')

            comment_detected = False

            if delimited_line_region[line_num][end_idx:end_idx + 2] == sql_comment_prefix:  # Accounts for the '--' char
                print('-- detected after')
                end_idx += len(sql_comment_prefix)
                comment_detected = True

            if tag.name in selected_keys:
                cur_line = delimited_line_region[line_num][end_idx:]
                if check_if_empty_line(cur_line):
                    line_num_deletion_list.append(line_num)
                else:
                    delimited_line_region[line_num] = delimited_line_region[line_num][end_idx:]
            else:
                prefix = ''
                if comment_detected:
                    # rollback prior to sql_comment_prefix
                    end_idx -= len(sql_comment_prefix)
                else:
                    prefix = sql_comment_prefix

                cur_line = delimited_line_region[line_num][end_idx:]
                if check_if_empty_line(cur_line):
                    line_num_deletion_list.append(line_num)
                else:
                    delimited_line_region[line_num] = prefix + delimited_line_region[line_num][end_idx:]

        if tag.name not in selected_keys:
            if type(tag) == BlockTag:
                start, end = tag.start.line_num, tag.end.line_num
                if tag.name not in selected_keys:
                    for line_num in range(start, end):
                        cur_line = delimited_line_region[line_num]
                        # check for any white space till comment
                        if re.search(r'[ ]*--', cur_line):
                            continue
                        if check_if_empty_line(cur_line):
                            line_num_deletion_list.append(line_num)
                            continue
                        else:
                            delimited_line_region[line_num] = sql_comment_prefix + delimited_line_region[line_num]
            elif not comment_detected:
                line_num = tag.line_num
                cur_line = delimited_line_region[line_num]
                if check_if_empty_line(cur_line):
                    line_num_deletion_list.append(line_num)
                    continue

    for offset, idx in enumerate(line_num_deletion_list):
        del delimited_line_region[idx - offset]

    print('Final output:')
    print('\n'.join(delimited_line_region))


def check_if_empty_line(line: str) -> str:
    space = ' '

    for i in range(len(line)):
        if line[i] != space:
            return False

    return True


def get_block_tag_overlap_ranges(block_tags):
    block_tag_lookup = dict()

    for tag in block_tags:
        if tag.name not in block_tag_lookup:
            block_tag_lookup[tag.name] = list()

        block_tag_lookup[tag.name].append([tag.start.line_num, tag.end.line_num])

    return block_tag_lookup


def check_for_interval_overlap(interval_dict):
    # If blah is enabled, then we need to ensure NOS is disabled and output disabled intervals
    # If blah and nos is enabled, then merge both intervals

    line_usage_lookup = set()

    for key, intervals in interval_dict.items():
        for interval in intervals:
            start, end = interval
            for i in range(start, end + 1):
                if i in line_usage_lookup:
                    raise Exception(
                        f'overlap detected for lines - {start + 1}:{end + 1} - Tags are restricted per line num')

                line_usage_lookup.add(i)

    return False


def get_interval_dict(tags=None, block_tags=None, dictionary=None):
    interval_dict = dict()
    if dictionary:
        interval_dict = dictionary

    if tags:
        for tag in tags:
            if tag.name not in interval_dict:
                interval_dict[tag.name] = list()
            interval_dict[tag.name].append([tag.line_num, tag.line_num])

    if block_tags:
        for btag in block_tags:
            if btag.name not in interval_dict:
                interval_dict[btag.name] = list()
            interval_dict[btag.name].append([btag.start.line_num, btag.end.line_num])

    return interval_dict

if __name__ == "__main__":
    import logging
    logger = logging.getLogger('main')
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    
    sql_parser = SqlFileParser('simple_query.sql', log_handler=logger.debug)
    sql_file = sql_parser.run(run_tags=[], exclude=['Tables'])

    sql_file.dump('simple_query_rendered.sql', comment_mode=True)
    print(sql_file.query_tags)
    print(sql_file.line_tags)
    print(sql_file.block_tags)
    print(sql_file.to_list())
