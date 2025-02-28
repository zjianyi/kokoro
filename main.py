"""
Main entry point for the Twitter agent.
"""
import os
import json
import argparse
import logging
from dotenv import load_dotenv

# Import custom modules
from twitter_agent import TwitterAgent
from custom_twitter_actions import setup_twitter_client
from hyperbolic_compute import setup_hyperbolic_compute, initialize_hyperbolic_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_character_config(character_file: str) -> dict:
    """
    Load character configuration from a JSON file.
    
    Args:
        character_file: Path to the character configuration file
        
    Returns:
        Dictionary containing character configuration
    """
    try:
        with open(character_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load character configuration: {str(e)}")
        raise

def main():
    """Main entry point for the Twitter agent."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Twitter agent powered by Hyperbolic")
    parser.add_argument("--character", type=str, default="character.json",
                       help="Path to character configuration file")
    parser.add_argument("--test-mode", action="store_true",
                       help="Run in test mode without Hyperbolic compute")
    parser.add_argument("--post-tweet", type=str,
                       help="Post a single tweet with the given content")
    parser.add_argument("--reply-to", type=str,
                       help="Reply to a tweet with the given ID")
    parser.add_argument("--reply-content", type=str,
                       help="Content for the reply")
    parser.add_argument("--send-dm", type=str,
                       help="Send a direct message to the user with the given ID")
    parser.add_argument("--dm-content", type=str,
                       help="Content for the direct message")
    parser.add_argument("--search", type=str,
                       help="Search for tweets with the given query")
    parser.add_argument("--engage", type=str, choices=["reply", "retweet", "like", "all"],
                       help="Engagement action for search results")
    parser.add_argument("--tweet-interval", type=int, default=7200,
                       help="Interval between tweets in seconds (default: 7200 - 2 hours)")
    parser.add_argument("--mention-interval", type=int, default=300,
                       help="Interval between mention checks in seconds (default: 300 - 5 minutes)")
    parser.add_argument("--dm-interval", type=int, default=300,
                       help="Interval between DM checks in seconds (default: 300 - 5 minutes)")
    parser.add_argument("--max-daily-tweets", type=int, default=12,
                       help="Maximum number of tweets to post per day (default: 12)")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Load character configuration
    character = load_character_config(args.character)
    logger.info(f"Loaded character configuration for {character['name']}")
    
    # Set up Twitter client
    twitter_auth = {
        "consumer_key": os.environ.get("TWITTER_API_KEY"),
        "consumer_secret": os.environ.get("TWITTER_API_SECRET"),
        "access_token": os.environ.get("TWITTER_ACCESS_TOKEN"),
        "access_token_secret": os.environ.get("TWITTER_ACCESS_SECRET"),
        "bearer_token": os.environ.get("TWITTER_BEARER_TOKEN")
    }
    
    twitter_client = setup_twitter_client(twitter_auth)
    logger.info("Twitter client initialized")
    
    # Set up compute configuration
    compute_config = {
        "api_key": os.environ.get("HYPERBOLIC_API_KEY"),
        "model_id": os.environ.get("HYPERBOLIC_MODEL"),
        "test_mode": args.test_mode
    }
    
    # Initialize model
    if args.test_mode:
        logger.info("Running in test mode without Hyperbolic compute")
        model = {"client": None, "model_config": {"model_id": "test-model"}}
    else:
        # Set up Hyperbolic compute
        hyperbolic_client = setup_hyperbolic_compute(compute_config["api_key"])
        
        # Initialize model
        model = initialize_hyperbolic_model(
            hyperbolic_client, 
            model_id=compute_config["model_id"]
        )
        logger.info(f"Initialized model: {model['model_config']['model_id']}")
    
    # Create Twitter agent
    agent = TwitterAgent(
        twitter_client=twitter_client,
        character=character,
        model=model,
        compute_config=compute_config
    )
    
    # Handle command line actions
    if args.post_tweet:
        logger.info("Posting a single tweet")
        result = agent.post_single_tweet(args.post_tweet)
        if result["success"]:
            logger.info(f"Tweet posted successfully: {result['tweet_id']}")
        else:
            logger.error(f"Failed to post tweet: {result.get('error')}")
    
    elif args.reply_to and args.reply_content:
        logger.info(f"Replying to tweet {args.reply_to}")
        result = agent.reply_to_single_tweet(args.reply_to, args.reply_content)
        if result["success"]:
            logger.info(f"Reply posted successfully: {result['tweet_id']}")
        else:
            logger.error(f"Failed to post reply: {result.get('error')}")
    
    elif args.send_dm and args.dm_content:
        logger.info(f"Sending direct message to user {args.send_dm}")
        result = agent.send_single_dm(args.send_dm, args.dm_content)
        if result["success"]:
            logger.info(f"Direct message sent successfully: {result['message_id']}")
        else:
            logger.error(f"Failed to send direct message: {result.get('error')}")
    
    elif args.search and args.engage:
        logger.info(f"Searching for tweets with query: {args.search}")
        results = agent.search_and_engage(args.search, action=args.engage)
        logger.info(f"Engaged with {len(results)} tweets")
    
    else:
        # Start the agent in autonomous mode
        logger.info("Starting agent in autonomous mode")
        agent.start(
            mode="autonomous",
            posting_interval=args.tweet_interval,
            mention_check_interval=args.mention_interval,
            dm_check_interval=args.dm_interval,
            max_daily_tweets=args.max_daily_tweets
        )
        
        try:
            # Keep the main thread alive
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping agent")
            agent.stop()

if __name__ == "__main__":
    main() 