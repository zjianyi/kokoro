"""
Twitter API interaction functions for the Hyperbolic Twitter agent.
"""
import os
import tweepy
import logging
import requests
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_bearer_token(client_id: str, client_secret: str) -> str:
    """
    Get a bearer token using client credentials.
    
    Args:
        client_id: Twitter client ID
        client_secret: Twitter client secret
        
    Returns:
        Bearer token string
    """
    try:
        url = "https://api.twitter.com/oauth2/token"
        auth = (client_id, client_secret)
        data = {"grant_type": "client_credentials"}
        
        response = requests.post(url, auth=auth, data=data)
        response.raise_for_status()
        
        return response.json()["access_token"]
    except Exception as e:
        logger.error(f"Failed to get bearer token: {str(e)}")
        raise

def setup_twitter_client(auth_credentials: Dict[str, str]) -> Dict:
    """
    Sets up and authenticates a Twitter API client.
    
    Args:
        auth_credentials: Dictionary containing Twitter API credentials
            - consumer_key: Twitter API key (OAuth 1.0)
            - consumer_secret: Twitter API secret (OAuth 1.0)
            - access_token: Twitter access token (OAuth 1.0)
            - access_token_secret: Twitter access token secret (OAuth 1.0)
            - bearer_token: (Optional) Twitter bearer token (OAuth 2.0)
    
    Returns:
        Dictionary containing authenticated clients and auth objects
    """
    try:
        # Initialize result dictionary
        result = {
            "v2_client": None,
            "v1_api": None,
            "auth": None,
            "credentials": auth_credentials.copy()
        }
        
        # Check if bearer token is provided
        bearer_token = auth_credentials.get("bearer_token") or os.environ.get("TWITTER_BEARER_TOKEN")
        
        # Set up OAuth 1.0a authentication
        if all(key in auth_credentials for key in ["consumer_key", "consumer_secret", "access_token", "access_token_secret"]):
            logger.info("Setting up Twitter client with OAuth 1.0a")
            
            # Create OAuth 1.0a auth handler
            auth = tweepy.OAuth1UserHandler(
                consumer_key=auth_credentials["consumer_key"],
                consumer_secret=auth_credentials["consumer_secret"],
                access_token=auth_credentials["access_token"],
                access_token_secret=auth_credentials["access_token_secret"]
            )
            
            # Create API v1.1 instance
            v1_api = tweepy.API(auth)
            
            # Test the credentials
            try:
                v1_api.verify_credentials()
                logger.info("Twitter API v1.1 credentials verified successfully")
                result["v1_api"] = v1_api
                result["auth"] = auth
            except Exception as e:
                logger.warning(f"Failed to verify Twitter API v1.1 credentials: {str(e)}")
        
        # Set up v2 client with the best available authentication
        if bearer_token:
            logger.info("Setting up Twitter API v2 client with bearer token")
            
            if all(key in auth_credentials for key in ["consumer_key", "consumer_secret", "access_token", "access_token_secret"]):
                # Use both OAuth 1.0a and bearer token
                v2_client = tweepy.Client(
                    bearer_token=bearer_token,
                    consumer_key=auth_credentials["consumer_key"],
                    consumer_secret=auth_credentials["consumer_secret"],
                    access_token=auth_credentials["access_token"],
                    access_token_secret=auth_credentials["access_token_secret"]
                )
                logger.info("Twitter API v2 client authenticated with both bearer token and OAuth 1.0a")
            else:
                # Read-only client with bearer token
                v2_client = tweepy.Client(bearer_token=bearer_token)
                logger.info("Twitter API v2 client authenticated with bearer token (read-only)")
            
            result["v2_client"] = v2_client
        elif result["auth"] is not None:
            # Use OAuth 1.0a for v2 client if no bearer token
            v2_client = tweepy.Client(
                consumer_key=auth_credentials["consumer_key"],
                consumer_secret=auth_credentials["consumer_secret"],
                access_token=auth_credentials["access_token"],
                access_token_secret=auth_credentials["access_token_secret"]
            )
            logger.info("Twitter API v2 client authenticated with OAuth 1.0a")
            result["v2_client"] = v2_client
        
        if result["v2_client"] is None and result["v1_api"] is None:
            raise ValueError("Failed to authenticate with Twitter API using any method")
        
        logger.info("Twitter client setup completed successfully")
        return result
    except Exception as e:
        logger.error(f"Failed to authenticate Twitter client: {str(e)}")
        raise

def post_tweet(client, text, **kwargs):
    """
    Posts a tweet using the best available method.
    
    Args:
        client: Twitter client dictionary from setup_twitter_client
        text: Tweet text content
        **kwargs: Additional parameters for the tweet
        
    Returns:
        Dictionary with success status and tweet data or error
    """
    try:
        # Try using v1.1 API first (more reliable for posting)
        if client["v1_api"] is not None:
            logger.info("Attempting to post tweet using Twitter API v1.1")
            try:
                status = client["v1_api"].update_status(text)
                logger.info(f"Tweet posted successfully via API v1.1: {status.id}")
                return {
                    "success": True,
                    "tweet_id": status.id,
                    "created_at": status.created_at
                }
            except Exception as e1:
                logger.warning(f"Failed to post tweet via API v1.1: {str(e1)}")
                # Fall through to v2 API
        
        # Try using v2 API
        if client["v2_client"] is not None:
            logger.info("Attempting to post tweet using Twitter API v2")
            try:
                response = client["v2_client"].create_tweet(text=text, **kwargs)
                tweet_id = response.data["id"]
                logger.info(f"Tweet posted successfully via API v2: {tweet_id}")
                return {
                    "success": True,
                    "tweet_id": tweet_id
                }
            except Exception as e2:
                logger.error(f"Failed to post tweet via API v2: {str(e2)}")
                return {
                    "success": False,
                    "error": str(e2)
                }
        
        # If we get here, we couldn't post the tweet
        logger.error("No suitable API client available for posting tweets")
        return {
            "success": False,
            "error": "No suitable API client available for posting tweets"
        }
    except Exception as e:
        logger.error(f"Failed to post tweet: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def reply_to_tweet(client, content: str, tweet_id: str, 
                  media_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Replies to a specific tweet.
    
    Args:
        client: Twitter client dictionary from setup_twitter_client
        content: String content of the reply
        tweet_id: ID of the tweet to reply to
        media_ids: Optional list of media IDs to attach
    
    Returns:
        Dictionary containing response data including reply tweet ID
    """
    try:
        # Try using v2 API
        if client["v2_client"] is not None:
            logger.info("Attempting to reply to tweet using Twitter API v2")
            try:
                if media_ids:
                    response = client["v2_client"].create_tweet(
                        text=content,
                        media_ids=media_ids,
                        in_reply_to_tweet_id=tweet_id
                    )
                else:
                    response = client["v2_client"].create_tweet(
                        text=content,
                        in_reply_to_tweet_id=tweet_id
                    )
                
                tweet_id = response.data["id"]
                logger.info(f"Reply posted successfully via API v2: {tweet_id}")
                return {
                    "success": True,
                    "tweet_id": tweet_id,
                    "in_reply_to": tweet_id
                }
            except Exception as e2:
                logger.error(f"Failed to reply to tweet via API v2: {str(e2)}")
                # Fall through to v1.1 API
        
        # Try using v1.1 API as fallback
        if client["v1_api"] is not None:
            logger.info("Attempting to reply to tweet using Twitter API v1.1")
            try:
                status = client["v1_api"].update_status(
                    status=content,
                    in_reply_to_status_id=tweet_id,
                    auto_populate_reply_metadata=True
                )
                logger.info(f"Reply posted successfully via API v1.1: {status.id}")
                return {
                    "success": True,
                    "tweet_id": status.id,
                    "in_reply_to": tweet_id,
                    "created_at": status.created_at
                }
            except Exception as e1:
                logger.warning(f"Failed to reply to tweet via API v1.1: {str(e1)}")
                return {
                    "success": False,
                    "error": str(e1)
                }
        
        # If we get here, we couldn't reply to the tweet
        logger.error("No suitable API client available for replying to tweets")
        return {
            "success": False,
            "error": "No suitable API client available for replying to tweets"
        }
    except Exception as e:
        logger.error(f"Failed to reply to tweet: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def retweet(client, tweet_id: str) -> Dict[str, Any]:
    """
    Retweets a specific tweet.
    
    Args:
        client: Twitter client dictionary from setup_twitter_client
        tweet_id: ID of the tweet to retweet
    
    Returns:
        Dictionary containing response data
    """
    try:
        # Try using v2 API
        if client["v2_client"] is not None:
            logger.info("Attempting to retweet using Twitter API v2")
            try:
                response = client["v2_client"].retweet(tweet_id)
                logger.info(f"Successfully retweeted tweet {tweet_id} via API v2")
                return {
                    "success": True,
                    "retweet_id": response.data["id"]
                }
            except Exception as e2:
                logger.error(f"Failed to retweet via API v2: {str(e2)}")
                # Fall through to v1.1 API
        
        # Try using v1.1 API as fallback
        if client["v1_api"] is not None:
            logger.info("Attempting to retweet using Twitter API v1.1")
            try:
                status = client["v1_api"].retweet(tweet_id)
                logger.info(f"Successfully retweeted tweet {tweet_id} via API v1.1")
                return {
                    "success": True,
                    "retweet_id": status.id
                }
            except Exception as e1:
                logger.warning(f"Failed to retweet via API v1.1: {str(e1)}")
                return {
                    "success": False,
                    "error": str(e1)
                }
        
        # If we get here, we couldn't retweet
        logger.error("No suitable API client available for retweeting")
        return {
            "success": False,
            "error": "No suitable API client available for retweeting"
        }
    except Exception as e:
        logger.error(f"Failed to retweet: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def like_tweet(client, tweet_id: str) -> Dict[str, Any]:
    """
    Likes a specific tweet.
    
    Args:
        client: Twitter client dictionary from setup_twitter_client
        tweet_id: ID of the tweet to like
    
    Returns:
        Dictionary containing response data
    """
    try:
        # Try using v2 API
        if client["v2_client"] is not None:
            logger.info("Attempting to like tweet using Twitter API v2")
            try:
                client["v2_client"].like(tweet_id)
                logger.info(f"Successfully liked tweet {tweet_id} via API v2")
                return {
                    "success": True
                }
            except Exception as e2:
                logger.error(f"Failed to like tweet via API v2: {str(e2)}")
                # Fall through to v1.1 API
        
        # Try using v1.1 API as fallback
        if client["v1_api"] is not None:
            logger.info("Attempting to like tweet using Twitter API v1.1")
            try:
                client["v1_api"].create_favorite(tweet_id)
                logger.info(f"Successfully liked tweet {tweet_id} via API v1.1")
                return {
                    "success": True
                }
            except Exception as e1:
                logger.warning(f"Failed to like tweet via API v1.1: {str(e1)}")
                return {
                    "success": False,
                    "error": str(e1)
                }
        
        # If we get here, we couldn't like the tweet
        logger.error("No suitable API client available for liking tweets")
        return {
            "success": False,
            "error": "No suitable API client available for liking tweets"
        }
    except Exception as e:
        logger.error(f"Failed to like tweet: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def get_mentions(client, since_id: Optional[str] = None, 
                max_results: int = 100) -> Dict[str, Any]:
    """
    Retrieves recent mentions of the authenticated user.
    
    Args:
        client: Twitter client dictionary from setup_twitter_client
        since_id: Optional tweet ID to retrieve mentions after
        max_results: Maximum number of results to return (max 100)
    
    Returns:
        Dictionary containing mentions data
    """
    try:
        # Try using v2 API
        if client["v2_client"] is not None:
            logger.info("Attempting to get mentions using Twitter API v2")
            try:
                user_id = client["v2_client"].get_me().data.id
                response = client["v2_client"].get_users_mentions(
                    id=user_id,
                    since_id=since_id,
                    max_results=max_results
                )
                
                mentions = response.data if response.data else []
                logger.info(f"Retrieved {len(mentions)} mentions via API v2")
                
                return {
                    "success": True,
                    "mentions": mentions
                }
            except Exception as e2:
                logger.error(f"Failed to get mentions via API v2: {str(e2)}")
                # Fall through to v1.1 API
        
        # Try using v1.1 API as fallback
        if client["v1_api"] is not None:
            logger.info("Attempting to get mentions using Twitter API v1.1")
            try:
                mentions = client["v1_api"].mentions_timeline(
                    since_id=since_id,
                    count=max_results
                )
                
                logger.info(f"Retrieved {len(mentions)} mentions via API v1.1")
                
                return {
                    "success": True,
                    "mentions": mentions
                }
            except Exception as e1:
                logger.warning(f"Failed to get mentions via API v1.1: {str(e1)}")
                return {
                    "success": False,
                    "error": str(e1)
                }
        
        # If we get here, we couldn't get mentions
        logger.error("No suitable API client available for getting mentions")
        return {
            "success": False,
            "error": "No suitable API client available for getting mentions"
        }
    except Exception as e:
        logger.error(f"Failed to retrieve mentions: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def get_direct_messages(client, since_id: Optional[str] = None, 
                       max_results: int = 50) -> Dict[str, Any]:
    """
    Retrieves recent direct messages sent to the authenticated user.
    
    Args:
        client: Twitter client dictionary from setup_twitter_client
        since_id: Optional message ID to retrieve DMs after
        max_results: Maximum number of results to return
    
    Returns:
        Dictionary containing direct messages data
    """
    try:
        # Try using v1.1 API (v2 API doesn't have DM endpoints yet)
        if client["v1_api"] is not None:
            logger.info("Attempting to get direct messages using Twitter API v1.1")
            try:
                # Get direct messages
                dms = client["v1_api"].get_direct_messages(
                    count=max_results
                )
                
                logger.info(f"Retrieved {len(dms)} direct messages via API v1.1")
                
                # Filter messages if since_id is provided
                if since_id:
                    dms = [dm for dm in dms if int(dm.id) > int(since_id)]
                    logger.info(f"Filtered to {len(dms)} new direct messages since {since_id}")
                
                return {
                    "success": True,
                    "direct_messages": dms
                }
            except Exception as e1:
                logger.warning(f"Failed to get direct messages via API v1.1: {str(e1)}")
                
                # Check if this is a permissions error
                if "403 Forbidden" in str(e1) and "access to a subset of X API" in str(e1):
                    logger.warning("DM access requires Twitter API Premium access. This feature will be disabled.")
                    # Return empty list instead of trying alternative methods that will also fail
                    return {
                        "success": True,
                        "direct_messages": []
                    }
                
                # Try alternative method for DMs
                try:
                    logger.info("Attempting to get direct messages using alternative method")
                    
                    # Get events
                    events = client["v1_api"].get_direct_message_events(count=max_results)
                    
                    # Filter events if since_id is provided
                    if since_id:
                        events = [event for event in events if int(event.id) > int(since_id)]
                    
                    logger.info(f"Retrieved {len(events)} direct message events")
                    
                    return {
                        "success": True,
                        "direct_messages": events
                    }
                except Exception as e2:
                    logger.error(f"Failed to get direct message events: {str(e2)}")
                    return {
                        "success": False,
                        "error": f"Failed to get direct messages: {str(e1)}, and failed to get events: {str(e2)}"
                    }
        
        # If we get here, we couldn't get direct messages
        logger.error("No suitable API client available for getting direct messages")
        return {
            "success": False,
            "error": "No suitable API client available for getting direct messages"
        }
    except Exception as e:
        logger.error(f"Failed to retrieve direct messages: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def send_direct_message(client, recipient_id: str, text: str) -> Dict[str, Any]:
    """
    Sends a direct message to a specific user.
    
    Args:
        client: Twitter client dictionary from setup_twitter_client
        recipient_id: ID of the user to send the message to
        text: Content of the direct message
    
    Returns:
        Dictionary containing response data
    """
    try:
        # Try using v1.1 API (v2 API doesn't have DM endpoints yet)
        if client["v1_api"] is not None:
            logger.info(f"Attempting to send direct message to user {recipient_id}")
            try:
                # Send direct message
                dm = client["v1_api"].send_direct_message(
                    recipient_id=recipient_id,
                    text=text
                )
                
                logger.info(f"Successfully sent direct message to user {recipient_id}")
                
                return {
                    "success": True,
                    "message_id": dm.id
                }
            except Exception as e1:
                logger.warning(f"Failed to send direct message via API v1.1: {str(e1)}")
                
                # Check if this is a permissions error
                if "403 Forbidden" in str(e1) and "access to a subset of X API" in str(e1):
                    logger.warning("DM access requires Twitter API Premium access. This feature will be disabled.")
                    raise Exception(f"Cannot send DMs: {str(e1)}")
                
                # Try alternative method for sending DMs
                try:
                    logger.info("Attempting to send direct message using alternative method")
                    
                    # Create event
                    event = client["v1_api"].send_direct_message_new(
                        recipient_id=recipient_id,
                        text=text
                    )
                    
                    logger.info(f"Successfully sent direct message event to user {recipient_id}")
                    
                    return {
                        "success": True,
                        "message_id": event.id
                    }
                except Exception as e2:
                    logger.error(f"Failed to send direct message event: {str(e2)}")
                    return {
                        "success": False,
                        "error": f"Failed to send direct message: {str(e1)}, and failed to send event: {str(e2)}"
                    }
        
        # If we get here, we couldn't send the direct message
        logger.error("No suitable API client available for sending direct messages")
        return {
            "success": False,
            "error": "No suitable API client available for sending direct messages"
        }
    except Exception as e:
        logger.error(f"Failed to send direct message: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def search_tweets(client, query: str, max_results: int = 100) -> Dict[str, Any]:
    """
    Searches for tweets matching a query.
    
    Args:
        client: Twitter client dictionary from setup_twitter_client
        query: Search query string
        max_results: Maximum number of results to return
    
    Returns:
        Dictionary containing search results
    """
    try:
        # Try using v2 API
        if client["v2_client"] is not None:
            logger.info("Attempting to search tweets using Twitter API v2")
            try:
                response = client["v2_client"].search_recent_tweets(
                    query=query,
                    max_results=max_results
                )
                
                tweets = response.data if response.data else []
                logger.info(f"Found {len(tweets)} tweets matching query: {query} via API v2")
                
                return {
                    "success": True,
                    "tweets": tweets
                }
            except Exception as e2:
                logger.error(f"Failed to search tweets via API v2: {str(e2)}")
                # Fall through to v1.1 API
        
        # Try using v1.1 API as fallback
        if client["v1_api"] is not None:
            logger.info("Attempting to search tweets using Twitter API v1.1")
            try:
                tweets = client["v1_api"].search_tweets(
                    q=query,
                    count=max_results
                )
                
                logger.info(f"Found {len(tweets)} tweets matching query: {query} via API v1.1")
                
                return {
                    "success": True,
                    "tweets": tweets
                }
            except Exception as e1:
                logger.warning(f"Failed to search tweets via API v1.1: {str(e1)}")
                return {
                    "success": False,
                    "error": str(e1)
                }
        
        # If we get here, we couldn't search tweets
        logger.error("No suitable API client available for searching tweets")
        return {
            "success": False,
            "error": "No suitable API client available for searching tweets"
        }
    except Exception as e:
        logger.error(f"Failed to search tweets: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def get_user_timeline(client, username: str, max_results: int = 100) -> Dict[str, Any]:
    """
    Retrieves a user's timeline.
    
    Args:
        client: Twitter client dictionary from setup_twitter_client
        username: Twitter username without the @ symbol
        max_results: Maximum number of results to return
    
    Returns:
        Dictionary containing timeline tweets
    """
    try:
        # Try using v2 API
        if client["v2_client"] is not None:
            logger.info("Attempting to get user timeline using Twitter API v2")
            try:
                user = client["v2_client"].get_user(username=username)
                if not user.data:
                    return {
                        "success": False,
                        "error": f"User {username} not found"
                    }
                    
                user_id = user.data.id
                response = client["v2_client"].get_users_tweets(
                    id=user_id,
                    max_results=max_results
                )
                
                tweets = response.data if response.data else []
                logger.info(f"Retrieved {len(tweets)} tweets from {username}'s timeline via API v2")
                
                return {
                    "success": True,
                    "tweets": tweets
                }
            except Exception as e2:
                logger.error(f"Failed to get user timeline via API v2: {str(e2)}")
                # Fall through to v1.1 API
        
        # Try using v1.1 API as fallback
        if client["v1_api"] is not None:
            logger.info("Attempting to get user timeline using Twitter API v1.1")
            try:
                tweets = client["v1_api"].user_timeline(
                    screen_name=username,
                    count=max_results
                )
                
                logger.info(f"Retrieved {len(tweets)} tweets from {username}'s timeline via API v1.1")
                
                return {
                    "success": True,
                    "tweets": tweets
                }
            except Exception as e1:
                logger.warning(f"Failed to get user timeline via API v1.1: {str(e1)}")
                return {
                    "success": False,
                    "error": str(e1)
                }
        
        # If we get here, we couldn't get the user timeline
        logger.error("No suitable API client available for getting user timeline")
        return {
            "success": False,
            "error": "No suitable API client available for getting user timeline"
        }
    except Exception as e:
        logger.error(f"Failed to get user timeline: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        } 