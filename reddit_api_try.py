import praw

import tokens

reddit = praw.Reddit(client_id=tokens.client_id,
                     client_secret=tokens.secret_key, password=tokens.password,
                     user_agent=tokens.user_agent, username=tokens.username)

subreddit = reddit.subreddit('python')
hot_python = subreddit.hot(limit=30)

for submission in hot_python:
    if not submission.stickied:
        print(submission.title)
