import sys
import textwrap
import time

import praw
import requests as requests

import tokens

# read_only = true -> not logged in
MAX_LENGTH = 50
POST_METADATA = ['thumbnail', 'votes', 'content', 'reply', 'link', 'comments']
USER_METADATA = ['submissions', 'comments']


def setup_reddit():
    try:
        reddit_obj = praw.Reddit(client_id=tokens.client_id,
                                 client_secret=tokens.secret_key, password=tokens.password,
                                 user_agent=tokens.user_agent, username=tokens.username)
        return reddit_obj
    except:
        sys.exit("Error during Reddit setup!")


def get_filename(path):
    for chars in ['&', ':', '<', '>', '|', '/', '?', '!', '.']:
        if chars in path:
            path = path.replace(chars, '')
    path = ' '.join(path.split())
    for chars in [' ', '\n', '\0', '\t']:
        if chars in path:
            path = path.replace(chars, '_')
    return path


def formatted_submission(submission):
    text = []
    indent = 3
    wrap = textwrap.TextWrapper(initial_indent=indent * ' ' + '|', subsequent_indent=indent * ' ' + '|')
    br = indent * ' ' + '-' * (80 - indent)
    text.append(br)
    text += wrap.wrap(submission.title)
    text.append(br)
    if submission.selftext:
        text += wrap.wrap(submission.selftext)
        text.append(br)
    if submission.url:
        text += wrap.wrap(submission.url)
        text.append(br)
    d = get_post_metadata(submission)
    formatted = "[id:%(id)s] | %(author)s %(score)d points %(time)s ago"
    text += wrap.wrap(formatted % d)
    text.append(br)
    return '\n'.join(text) + '\n'


def formatted_comment(post, depth=0, cutoff=-1, recursive=True, top=-1):
    indent = 2
    base_ind = 4
    indent += depth * base_ind
    if depth == cutoff:
        return ' ' * indent + '...\n'
    text = ''
    comments = []
    post.comments.replace_more(limit=None)
    for top_level in post.comments:
        comments.extend(process_comment(top_level))
    for comment in comments:
        text += get_comment_header(comment[0], indent * comment[1])
        text += get_comment_body(comment[0], indent * comment[1])
        text += '\n********************************************************************************\n'
    return text


def process_comment(comment, depth=0):
    yield comment, depth
    for reply in comment.replies:
        yield from process_comment(reply, depth + 1)


def get_comment_header(comment, indent):
    wrap = indent * ' ' + (78 - indent) * '-'
    formatted = indent * ' ' + "| [id:%(id)s] | %(author)s %(score)d points %(time)s ago"
    d = get_post_metadata(comment)
    return '\n'.join([wrap, formatted % d, wrap]) + '\n'


def get_comment_body(comment, indent):
    wrap = indent * ' ' + (78 - indent) * '-' + '\n'
    indent = indent * ' '
    wrapper = textwrap.TextWrapper(initial_indent=indent + '|', subsequent_indent=indent + '|', width=80)
    return '\n'.join(wrapper.wrap(comment.body) + [wrap])


def get_post_metadata(post):
    metadata = {'author': post.author if post.author else "REMOVED",
                'time': time.ctime(post.created),
                'score': post.score, 'id': post.id}
    return metadata


def get_file_content(path, post):
    data = ''
    splitted_path = path.split('/')
    if splitted_path[-1] == 'content':
        data = formatted_submission(post)
        data = data.encode('ascii', 'ignore')
    elif splitted_path[-1] == 'votes':
        data = str(post.score) + '\n'
        data = data.encode('ascii', 'ignore')
    elif splitted_path[-1] == 'comments':
        data = formatted_comment(post)
        data = data.encode('ascii', 'ignore')
    elif (splitted_path[-1] == 'thumbnail' and 'thumbnail' in dir(post) and post.thumbnail not in ['', 'self',
                                                                                                   'default']):
        f = requests.get(post.thumbnail)
        if f.status_code == 200:
            data = f.content
    elif splitted_path[-1] == 'link' and post.url:
        f = requests.get(post.url)
        if f.status_code == 200:
            data = f.content
    return data
