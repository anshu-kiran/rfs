import sys

import praw

import tokens


class RFS:
    def __init__(self, reddit):
        self.reddit = reddit

    def check_reddit_read_only(self):
        print(self.reddit.read_only)


def setup_reddit():
    try:
        reddit_obj = praw.Reddit(client_id=tokens.client_id,
                                 client_secret=tokens.secret_key, password=tokens.password,
                                 user_agent=tokens.user_agent, username=tokens.username)
        return reddit_obj
    except:
        sys.exit("Error during Reddit setup!")


if __name__ == '__main__':
    reddit_login = setup_reddit()
    rfs = RFS(reddit_login)
    rfs.check_reddit_read_only()
