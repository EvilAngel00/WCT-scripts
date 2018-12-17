import praw

reddit = praw.Reddit(client_id='',
                     client_secret='',
                     password='',
                     user_agent='comps_post_script by /u/TheWCAOfficial',
                     username='TheWCAOfficial')
                     
reddit.subreddit('rui_tests').submit('Some title', selftext='Some text')