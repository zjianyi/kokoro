"""
Test script to check Twitter API access levels.
"""
import os
import tweepy
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_twitter_api_access():
    """Test various Twitter API endpoints to determine access levels."""
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    consumer_key = os.environ["TWITTER_API_KEY"]
    consumer_secret = os.environ["TWITTER_API_SECRET"]
    access_token = os.environ["TWITTER_ACCESS_TOKEN"]
    access_token_secret = os.environ["TWITTER_ACCESS_SECRET"]
    bearer_token = os.environ["TWITTER_BEARER_TOKEN"]
    
    logger.info("Testing Twitter API access with different authentication methods...")
    
    # Test OAuth 1.0a authentication
    try:
        logger.info("Testing OAuth 1.0a authentication...")
        auth = tweepy.OAuth1UserHandler(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        api_v1 = tweepy.API(auth)
        
        # Test verify_credentials
        try:
            user = api_v1.verify_credentials()
            logger.info(f"OAuth 1.0a authentication successful - User: @{user.screen_name}")
        except Exception as e:
            logger.error(f"OAuth 1.0a verify_credentials failed: {str(e)}")
        
        # Test home timeline
        try:
            tweets = api_v1.home_timeline(count=1)
            logger.info(f"OAuth 1.0a home_timeline successful - Retrieved {len(tweets)} tweets")
        except Exception as e:
            logger.error(f"OAuth 1.0a home_timeline failed: {str(e)}")
        
        # Test user timeline
        try:
            tweets = api_v1.user_timeline(count=1)
            logger.info(f"OAuth 1.0a user_timeline successful - Retrieved {len(tweets)} tweets")
        except Exception as e:
            logger.error(f"OAuth 1.0a user_timeline failed: {str(e)}")
        
        # Test update status (post tweet)
        try:
            status = api_v1.update_status("This is a test tweet from the Twitter API v1.1 using OAuth 1.0a. #APITest")
            logger.info(f"OAuth 1.0a update_status successful - Tweet ID: {status.id}")
        except Exception as e:
            logger.error(f"OAuth 1.0a update_status failed: {str(e)}")
    
    except Exception as e:
        logger.error(f"OAuth 1.0a authentication setup failed: {str(e)}")
    
    # Test OAuth 2.0 authentication with bearer token
    try:
        logger.info("\nTesting OAuth 2.0 authentication with bearer token...")
        client_v2 = tweepy.Client(bearer_token=bearer_token)
        
        # Test get user
        try:
            user = client_v2.get_me()
            logger.info(f"OAuth 2.0 get_me successful - User ID: {user.data.id}")
        except Exception as e:
            logger.error(f"OAuth 2.0 get_me failed: {str(e)}")
        
        # Test get tweets
        try:
            tweets = client_v2.get_users_tweets(id=client_v2.get_me().data.id)
            logger.info(f"OAuth 2.0 get_users_tweets successful - Retrieved {len(tweets.data) if tweets.data else 0} tweets")
        except Exception as e:
            logger.error(f"OAuth 2.0 get_users_tweets failed: {str(e)}")
        
        # Test create tweet
        try:
            tweet = client_v2.create_tweet(text="This is a test tweet from the Twitter API v2 using OAuth 2.0 bearer token. #APITest")
            logger.info(f"OAuth 2.0 create_tweet successful - Tweet ID: {tweet.data['id']}")
        except Exception as e:
            logger.error(f"OAuth 2.0 create_tweet failed: {str(e)}")
    
    except Exception as e:
        logger.error(f"OAuth 2.0 authentication setup failed: {str(e)}")
    
    # Test combined OAuth 1.0a and OAuth 2.0 authentication
    try:
        logger.info("\nTesting combined OAuth 1.0a and OAuth 2.0 authentication...")
        client_combined = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # Test get user
        try:
            user = client_combined.get_me()
            logger.info(f"Combined auth get_me successful - User ID: {user.data.id}")
        except Exception as e:
            logger.error(f"Combined auth get_me failed: {str(e)}")
        
        # Test create tweet
        try:
            tweet = client_combined.create_tweet(text="This is a test tweet from the Twitter API v2 using combined OAuth 1.0a and OAuth 2.0 authentication. #APITest")
            logger.info(f"Combined auth create_tweet successful - Tweet ID: {tweet.data['id']}")
        except Exception as e:
            logger.error(f"Combined auth create_tweet failed: {str(e)}")
    
    except Exception as e:
        logger.error(f"Combined authentication setup failed: {str(e)}")

if __name__ == "__main__":
    test_twitter_api_access() 