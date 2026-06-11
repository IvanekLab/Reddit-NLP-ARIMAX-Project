"""Reddit data collection for H5N1 research.

Collects posts and their comments from a set of bird-flu-related subreddits
using the Reddit API (via PRAW) and saves each subreddit's data to a CSV file.

API credentials are read from environment variables so that no secrets are
committed to source control. See ``.env.example`` for the required variables.

Guide for obtaining Reddit API keys:
https://medium.com/@archanakkokate/scraping-reddit-data-using-python-and-praw-a-beginners-guide-7047962f5d29

Usage:
    python reddit_collection.py
"""

import os

import pandas as pd
import praw

try:
    # Optional: load credentials from a local .env file if python-dotenv is
    # installed. Not required if the variables are already set in the shell.
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Subreddits to collect, mapped to the output CSV filename for each.
SUBREDDITS = {
    "Birdflu": "df_birdflu.csv",
    "H5N1_AvianFlu": "df_h5n1.csv",
    "BirdFluPreps": "df_birdflupreps.csv",
}

# Maximum number of top posts to fetch per subreddit.
POST_LIMIT = 900


def get_reddit_client():
    """Create an authenticated read-only Reddit client.

    Credentials are loaded from the following environment variables:
        REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

    Returns:
        praw.Reddit: An authenticated Reddit instance.

    Raises:
        RuntimeError: If any required environment variable is missing.
    """
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT")

    missing = [
        name
        for name, value in (
            ("REDDIT_CLIENT_ID", client_id),
            ("REDDIT_CLIENT_SECRET", client_secret),
            ("REDDIT_USER_AGENT", user_agent),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing required environment variable(s): "
            + ", ".join(missing)
            + ". See .env.example for setup instructions."
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        check_for_async=False,
    )


def collect_subreddit(reddit, subreddit_name, post_limit=POST_LIMIT):
    """Collect posts and all comments from a single subreddit.

    Args:
        reddit (praw.Reddit): An authenticated Reddit client.
        subreddit_name (str): Name of the subreddit to collect from.
        post_limit (int): Maximum number of top posts to fetch.

    Returns:
        pandas.DataFrame: One row per comment, with post and comment metadata.
    """
    subreddit = reddit.subreddit(subreddit_name)
    records = []

    for post in subreddit.top(limit=post_limit):
        # Expand every "load more comments" link so all comments are captured.
        post.comments.replace_more(limit=None)
        for comment in post.comments.list():
            records.append(
                {
                    "subreddit": subreddit_name,
                    "post_id": post.id,
                    "post_title": post.title,
                    "post_text": post.selftext,
                    "post_score": post.score,
                    "post_created_utc": post.created_utc,
                    "comment_id": comment.id,
                    "comment_body": comment.body,
                    "comment_score": comment.score,
                    "comment_created_utc": comment.created_utc,
                }
            )

    return pd.DataFrame(records)


def main():
    """Collect data from all configured subreddits and write CSV files."""
    reddit = get_reddit_client()

    # Quick authentication / connectivity check.
    print("Authenticated as:", reddit.user.me())

    for subreddit_name, output_path in SUBREDDITS.items():
        print(f"Collecting r/{subreddit_name} ...")
        df = collect_subreddit(reddit, subreddit_name)
        df.to_csv(output_path, index=False)
        print(
            f"  Saved {len(df)} comments from {df['post_id'].nunique()} posts "
            f"to {output_path}"
        )


if __name__ == "__main__":
    main()
