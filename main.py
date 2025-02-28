"""
Main entry point for the Twitter agent.
"""
import os
import json
import argparse
import logging
from dotenv import load_dotenv
from datetime import datetime
import time

# Import custom modules
from twitter_agent import TwitterAgent
from custom_twitter_actions import setup_twitter_client
from hyperbolic_compute import setup_hyperbolic_compute, initialize_hyperbolic_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"twitter_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
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
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Twitter Agent CLI")
    parser.add_argument("--character", type=str, default="characters/crypto_insight_bot.json", 
                        help="Path to character configuration JSON file")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode without Hyperbolic compute")
    parser.add_argument("--post-tweet", type=str, help="Post a tweet with the specified text")
    parser.add_argument("--reply-to", type=str, help="Reply to a tweet with the specified ID")
    parser.add_argument("--reply-text", type=str, help="Text for the reply")
    parser.add_argument("--send-dm", type=str, help="Send a DM to the specified user ID")
    parser.add_argument("--dm-text", type=str, help="Text for the DM")
    parser.add_argument("--search", type=str, help="Search for tweets with the specified query")
    parser.add_argument("--engage", action="store_true", help="Engage with search results")
    parser.add_argument("--tweet-interval", type=int, default=7200, 
                        help="Interval between tweets in seconds (default: 7200 = 2 hours)")
    parser.add_argument("--mention-interval", type=int, default=300, 
                        help="Interval between mention checks in seconds (default: 300 = 5 minutes)")
    parser.add_argument("--dm-interval", type=int, default=300, 
                        help="Interval between DM checks in seconds (default: 300 = 5 minutes)")
    parser.add_argument("--max-daily-tweets", type=int, default=12, 
                        help="Maximum number of tweets per day (default: 12)")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"twitter_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        ]
    )
    
    # Load character configuration
    character_config = load_character_config(args.character)
    logging.info(f"Loaded character configuration for {character_config.get('name', 'Unknown')}")
    
    # Initialize Twitter client
    twitter_client = setup_twitter_client()
    logging.info("Twitter client initialized")
    
    # Set up Hyperbolic compute if not in test mode
    if not args.test_mode:
        hyperbolic_api_key = os.getenv("HYPERBOLIC_API_KEY")
        if not hyperbolic_api_key:
            logging.error("HYPERBOLIC_API_KEY not found in environment variables")
            return
            
        hyperbolic_model = os.getenv("HYPERBOLIC_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
        
        try:
            hyperbolic_client = setup_hyperbolic_compute(hyperbolic_api_key)
            model_config = initialize_hyperbolic_model(hyperbolic_client, hyperbolic_model)
            logging.info(f"Initialized Hyperbolic compute with model: {hyperbolic_model}")
        except Exception as e:
            logging.error(f"Failed to initialize Hyperbolic compute: {str(e)}")
            logging.info("Falling back to test mode")
            args.test_mode = True
            model_config = None
    else:
        logging.info("Running in test mode without Hyperbolic compute")
        model_config = None
    
    # Create Twitter agent
    agent = TwitterAgent(
        twitter_client=twitter_client,
        character_config=character_config,
        model_config=model_config,
        test_mode=args.test_mode
    )
    
    # Handle command line actions
    if args.post_tweet:
        try:
            tweet_id = agent.post_tweet(args.post_tweet)
            logging.info(f"Tweet posted successfully: {tweet_id}")
        except Exception as e:
            logging.error(f"Failed to post tweet: {str(e)}")
    elif args.reply_to and args.reply_text:
        try:
            reply_id = agent.reply_to_tweet(args.reply_to, args.reply_text)
            logging.info(f"Reply posted successfully: {reply_id}")
        except Exception as e:
            logging.error(f"Failed to post reply: {str(e)}")
    elif args.send_dm and args.dm_text:
        try:
            result = agent.send_direct_message(args.send_dm, args.dm_text)
            if result:
                logging.info(f"DM sent successfully to user {args.send_dm}")
            else:
                logging.error(f"Failed to send DM to user {args.send_dm}")
        except Exception as e:
            if "403 Forbidden" in str(e) and "access to a subset of X API" in str(e):
                logging.error("Cannot send DMs: Your Twitter API access level does not support DM functionality")
            else:
                logging.error(f"Failed to send DM: {str(e)}")
    elif args.search:
        try:
            tweets = agent.search_tweets(args.search)
            logging.info(f"Found {len(tweets)} tweets matching query: {args.search}")
            
            if args.engage and tweets:
                for tweet in tweets[:5]:  # Engage with up to 5 tweets
                    try:
                        agent.engage_with_tweet(tweet.id)
                        logging.info(f"Engaged with tweet: {tweet.id}")
                        time.sleep(5)  # Add delay to avoid rate limits
                    except Exception as e:
                        logging.error(f"Failed to engage with tweet {tweet.id}: {str(e)}")
        except Exception as e:
            logging.error(f"Failed to search tweets: {str(e)}")
    else:
        # Start agent in autonomous mode
        logging.info("Starting agent in autonomous mode")
        try:
            agent.start(
                post_interval=args.tweet_interval,
                mention_check_interval=args.mention_interval,
                dm_check_interval=args.dm_interval,
                max_daily_tweets=args.max_daily_tweets
            )
            
            # Keep main thread alive
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                logging.info("Keyboard interrupt detected, stopping agent")
                agent.stop()
        except Exception as e:
            logging.error(f"Error in autonomous mode: {str(e)}")
            agent.stop()

if __name__ == "__main__":
    main() 