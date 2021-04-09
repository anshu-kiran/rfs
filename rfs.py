import errno
import stat
import time

import fuse
import requests

import utils

fuse.fuse_python_api = (0, 2)


class RFS(fuse.Fuse):
    def __init__(self, reddit, *args, **kw):
        print({'******************** INIT ********************'})
        super().__init__(*args, **kw)
        self.reddit = reddit

    def getattr(self, path):
        print({'******************** GETATTR ********************'})
        st = fuse.Stat()
        st.st_nlink = 2
        st.st_atime = int(time.time())
        st.st_mtime = st.st_atime
        st.st_ctime = st.st_atime

        st.st_mode = stat.S_IFREG | 0o0444

        splitted_path = path.split('/')
        path_length = len(splitted_path)

        if splitted_path[-1] == '.' or splitted_path[-1] == '..':
            st.st_mode = stat.S_IFDIR | 0o0555

        if path in ['/', '/u', '/r']:
            st.st_mode = stat.S_IFDIR | 0o0555

        if splitted_path[1] == 'r':
            if path_length == 3:
                my_subs = [sub.display_name.lower() for sub in self.reddit.user.subreddits()]
                if (path.split('/')[-1]).lower() not in my_subs:
                    st = -2
                else:
                    st.st_mode = stat.S_IFDIR | 0o0555

            elif path_length == 4:
                if splitted_path[-1] == 'post':  # file
                    st.st_mode = stat.S_IFREG | 0o0666
                else:  # folders
                    st.st_mode = stat.S_IFDIR | 0o0555
                return st

            elif path_length == 5 and splitted_path[-1] in utils.POST_METADATA:
                st.st_mode = stat.S_IFREG | 0o0444
                post_id = splitted_path[3].split('_')[-1]
                post = self.reddit.submission(post_id)
                formatted = ''
                if splitted_path[-1] == 'content':
                    formatted = utils.formatted_submission(post)
                    formatted = formatted.encode('ascii', 'ignore')
                elif splitted_path[-1] == 'votes':
                    formatted = str(post.score) + '\n'
                    formatted = formatted.encode('ascii', 'ignore')
                elif splitted_path[-1] == 'comments':
                    formatted = utils.formatted_comment(post)
                    formatted = formatted.encode('ascii', 'ignore')
                elif (splitted_path[-1] == 'thumbnail' and 'thumbnail' in dir(post)
                      and post.thumbnail != '' and post.thumbnail != 'self'
                      and post.thumbnail != 'default'):
                    f = requests.get(post.thumbnail)
                    if f.status_code == 200:
                        formatted = f.content
                elif splitted_path[-1] == 'link' and post.url:
                    f = requests.get(post.url)
                    if f.status_code == 200:
                        formatted = f.content
                elif splitted_path[-1] == 'reply':
                    st.st_mode = stat.S_IFREG | 0o0666
                st.st_size = len(formatted)

        if splitted_path[1] == 'u':
            if path_length == 3:
                st.st_mode = stat.S_IFDIR | 0o0555

            elif path_length == 4:
                st.st_mode = stat.S_IFDIR | 0o0555

            elif path_length == 5:
                st.st_mode = stat.S_IFLNK | 0o0777

        return st

    def readdir(self, path, offset):
        print({'******************** READDIR ********************'})
        yield fuse.Direntry('.')
        yield fuse.Direntry('..')

        splitted_path = path.split('/')
        path_length = len(splitted_path)

        if path == '/':
            yield fuse.Direntry('u')
            yield fuse.Direntry('r')
        elif splitted_path[1] == 'r':  # mnt/r/
            if path_length == 2:
                if not self.reddit.read_only:
                    for subreddit in self.reddit.user.subreddits(limit=utils.MAX_LENGTH):
                        subreddit_url = subreddit.url.split('/')[2]
                        yield fuse.Direntry(subreddit_url)
                else:
                    for subreddit in self.reddit.subreddits.default(limit=utils.MAX_LENGTH):
                        subreddit_url = subreddit.url.split('/')[2]
                        yield fuse.Direntry(subreddit_url)

            elif path_length == 3:  # mnt/r/<subname>
                subreddit = splitted_path[2]
                for post in self.reddit.subreddit(subreddit).hot(limit=utils.MAX_LENGTH):
                    filename = utils.sanitize_filepath(f'{post.title[:utils.MAX_LENGTH]} {post.id}')
                    yield fuse.Direntry(filename)
                yield fuse.Direntry('post')

            elif path_length == 4:  # mnt/r/<subname>/<post>
                post_id = splitted_path[3].replace('"', '').split('_')[-1]
                post = self.reddit.submission(post_id)
                for item in utils.POST_METADATA:
                    if item != 'thumbnail' and item != 'link':
                        yield fuse.Direntry(item)
                if post.thumbnail != "" and post.thumbnail != 'self' and post.thumbnail != 'default':
                    yield fuse.Direntry('thumbnail')
                    yield fuse.Direntry('link')

        elif splitted_path[1] == 'u':  # /mnt/u
            if path_length == 2:
                yield fuse.Direntry(self.reddit.user.me().name)

            elif path_length == 3:
                for item in utils.USER_METADATA:
                    yield fuse.Direntry(item)

            elif path_length == 4:
                redditor = self.reddit.redditor(splitted_path[2])
                if splitted_path[3] == 'submissions':
                    for post in redditor.submissions.top(limit=utils.MAX_LENGTH):
                        filename = utils.sanitize_filepath(f'{post.title[:utils.MAX_LENGTH]} {post.id}')
                        yield fuse.Direntry(filename)
                if splitted_path[3] == 'comments':
                    for post in redditor.submissions.top(limit=utils.MAX_LENGTH):
                        filename = utils.sanitize_filepath(f'{post.title[:utils.MAX_LENGTH]} {post.id}')
                        yield fuse.Direntry(filename)

    def mkdir(self, path, mode):
        print({'******************** MKDIR ********************'})
        try:
            sub = path.split('/')[-1]
            self.reddit.subreddit(sub).subscribe()
            return
        except:
            return -errno.ENOSYS

    def rmdir(self, path):
        print({'******************** RMDIR ********************'})
        try:
            sub = path.split('/')[-1]
            self.reddit.subreddit(sub).unsubscribe()
            return
        except:
            return -errno.ENOSYS

    def read(self, path, length, offset, fh=None):
        print({'******************** READ ********************'})
        formatted = []
        splitted_path = path.split('/')
        path_length = len(splitted_path)

        if splitted_path[1] == 'r':
            if path_length == 5:
                post_id = splitted_path[3].split('_')[-1]
                post = self.reddit.submission(post_id)

                formatted = ''
                if splitted_path[-1] == 'content':
                    formatted = utils.formatted_submission(post)
                    formatted = formatted.encode('ascii', 'ignore')
                elif splitted_path[-1] == 'votes':
                    formatted = str(post.score) + '\n'
                    formatted = formatted.encode('ascii', 'ignore')
                elif splitted_path[-1] == 'comments':
                    formatted = utils.formatted_comment(post)
                    formatted = formatted.encode('ascii', 'ignore')
                elif (splitted_path[-1] == 'thumbnail' and post.thumbnail != '' and
                      post.thumbnail != 'self' and post.thumbnail != 'default'):
                    f = requests.get(post.url)
                    if f.status_code == 200:
                        formatted = f.content
                elif splitted_path[-1] == 'link' and post.url:
                    f = requests.get(post.url)
                    if f.status_code == 200:
                        formatted = f.content
        return formatted[offset:offset + length]

    def readlink(self, path):
        print({'******************** READLINK ********************'})
        splitted_path = path.split('/')
        path_length = len(splitted_path)
        dots = ''

        if splitted_path[-1:][0][-1:] == '_' and path_length >= 5:
            path_length -= 2
            while path_length > 0:
                dots += '../'
                path_length -= 1
            return f'{dots}u/{splitted_path[-1:][0][11:-1]}'

        if splitted_path[1] == 'u' and path_length == 5:
            path_length -= 2
            while path_length > 0:
                dots += '../'
                path_length -= 1
            comment_id = path.split('_')[-1]
            post = self.reddit.submission(comment_id)
            subreddit = post.subreddit
            post_id = post.id
            return f'{dots}r/{subreddit}/{post_id}'

    def write(self, path, buffer, offset, fh=None):
        print({'******************** WRITE ********************'})
        splitted_path = path.split('/')

        if splitted_path[1] == 'r':
            if splitted_path[-1] == 'votes':
                post = self.reddit.submission(splitted_path[-2].split('_')[-1])
                vote = int(buffer)
                if vote == 0:
                    post.clear_vote()
                elif vote > 0:
                    post.upvote()
                elif vote < 0:
                    post.downvote()
                return len(buffer)

            if splitted_path[-1] == 'reply':
                post = self.reddit.submission(splitted_path[-2].split('_')[-1])
                post.reply(buffer)
                return len(buffer)

            if splitted_path[-1] == 'post':
                self.reddit.validate_on_submit = True
                print(buffer)
                print(buffer.decode().split('##'))
                buffer_split = buffer.decode().split('##')
                title = buffer_split[0].strip()
                text = buffer_split[1].strip()
                if text.startswith('https') or text.startswith('http') or text.startswith('www'):
                    self.reddit.subreddit(splitted_path[2]).submit(title=title, url=text)
                else:
                    self.reddit.subreddit(splitted_path[2]).submit(title=title, selftext=text)
                return len(buffer)


if __name__ == '__main__':
    reddit_login = utils.setup_reddit()
    rfs = RFS(reddit_login, dash_s_do='setsingle')
    rfs.parse()
    rfs.main()
