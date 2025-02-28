"""
Simple script to test posting a tweet.
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

def post_test_tweet():
    """Post a test tweet using OAuth 1.0a authentication."""
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    consumer_key = os.environ["TWITTER_API_KEY"]
    consumer_secret = os.environ["TWITTER_API_SECRET"]
    access_token = os.environ["TWITTER_ACCESS_TOKEN"]
    access_token_secret = os.environ["TWITTER_ACCESS_SECRET"]
    
    logger.info("Setting up Twitter client with OAuth 1.0a...")
    
    # Create OAuth 1.0a auth handler
    auth = tweepy.OAuth1UserHandler(
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )
    
    # Create API v1.1 instance
    api = tweepy.API(auth)
    
    # Test the credentials
    try:
        user = api.verify_credentials()
        logger.info(f"Authentication successful - User: @{user.screen_name}")
    except Exception as e:
        logger.error(f"Authentication failed: {str(e)}")
        return
    
    # Try to post a tweet
    try:
        tweet_text = "Testing my CryptoInsightBot with updated app permissions! #Crypto #Bitcoin #Test"
        status = api.update_status(tweet_text)
        logger.info(f"Tweet posted successfully! Tweet ID: {status.id}")
        logger.info(f"Tweet URL: https://twitter.com/{user.screen_name}/status/{status.id}")
    except Exception as e:
        logger.error(f"Failed to post tweet: {str(e)}")
        
        # Try with v2 API as fallback
        try:
            logger.info("Trying with Twitter API v2...")
            client = tweepy.Client(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            
            response = client.create_tweet(text=tweet_text)
            tweet_id = response.data["id"]
            logger.info(f"Tweet posted successfully via API v2! Tweet ID: {tweet_id}")
            logger.info(f"Tweet URL: https://twitter.com/{user.screen_name}/status/{tweet_id}")
        except Exception as e2:
            logger.error(f"Failed to post tweet via API v2: {str(e2)}")
            logger.error("\nIMPORTANT: You need to update your Twitter Developer App permissions:")
            logger.error("1. Go to https://developer.twitter.com/en/portal/dashboard")
            logger.error("2. Select your app")
            logger.error("3. Go to 'App settings' > 'App permissions'")
            logger.error("4. Change the app permissions from 'Read' to 'Read and Write'")
            logger.error("5. Save changes")
            logger.error("6. Regenerate your access tokens after changing permissions")

if __name__ == "__main__":
    post_test_tweet() 