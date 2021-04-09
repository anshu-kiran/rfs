# RFs - Reddit implementation of FUSE

To run Reddit implementation of FUSE on your system first run the following commands:

    sudo apt-get install libfuse-dev
    sudo apt-get build-dep python-fuse

Then after extracting, run the following commands:

    cd rfs/ && python3 -m venv venv/ && source venv/bin/activate
    pip install -r requirements.txt

Then, create a file `tokens.py` file and copy contents of `tokens_example.py` to it and fill with your credentials.

Create a mountpoint for reddit

    mkdir mnt

To mount reddit at mountpoint `mnt`, run the following command:

     python ./rfs.py mnt

Reddit can be browsed inside mnt folder. `r` folder cotains subreddit 
information while `u` contains user information. Commands used to access 
files are used to browse reddit. `cat` lists the contents of file while
`echo` is used to post/reply/upvote/downvote. `mkdir` subs to a subreddit 
while `rmdir` unsubs.

Some command examples:
    
    echo 1 >> votes
    mkdir diwhy
    rmdir diwhy
    echo "This is reply" >> reply
    echo "This is post Title ## This is post body" >> post
    cat comments

To unmount run:

    fusermount -u mnt
