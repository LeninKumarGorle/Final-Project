def is_valid_post(post, min_text_length=50):
    """
    Validate a Reddit post dictionary before processing or storing.
    """

    #check for required fields
    required_keys = ["id", "title", "selftext", "subreddit"]
    for key in required_keys:
        if key not in post or not post[key]:
            print(f"Missing required field: {key} in post: {post}")
            return False
    
    #check for removed/deleted/empty posts
    text = post["selftext"].strip()
    lowered_text = text.lower()

    if lowered_text in ["[removed]", "[deleted]", ""]:
        print(f"Skipping removed/deleted/empty post: {post['id']}")
        return False

    #avoid redundant posts
    if post["title"].strip().lower() == lowered_text:
        print(f"Post title and body are identical, skipping: {post['id']}")
        return False

    #minimum length check
    if len(text) < min_text_length:
        print(f"Post text too short (length={len(text)}), skipping: {post['id']}")
        return False

    return True
