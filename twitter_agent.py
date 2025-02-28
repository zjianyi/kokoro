"""
Core Twitter agent implementation using Hyperbolic's infrastructure.
"""
import os
import json
import time
import logging
import threading
import tweepy
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta

# Import custom modules
from custom_twitter_actions import (
    setup_twitter_client, post_tweet, reply_to_tweet, 
    retweet, like_tweet, get_mentions, search_tweets, get_user_timeline,
    get_direct_messages, send_direct_message
)
from hyperbolic_compute import (
    HyperbolicClient, setup_hyperbolic_compute, 
    initialize_hyperbolic_model, optimize_costs
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TwitterAgent:
    """Twitter agent powered by Hyperbolic's GPU marketplace."""
    
    def __init__(self, twitter_client: Dict[str, Any], character: Dict[str, Any], 
                model: Dict[str, Any], compute_config: Dict[str, Any]):
        """
        Initialize the Twitter agent.
        
        Args:
            twitter_client: Dictionary containing Twitter clients and auth objects
            character: Agent personality configuration
            model: Initialized language model configuration
            compute_config: Hyperbolic compute configuration
        """
        self.twitter_client = twitter_client
        self.character = character
        self.model = model
        self.compute_config = compute_config
        
        # Check if running in test mode
        self.test_mode = compute_config.get("test_mode", False)
        
        # Initialize state variables
        self.running = False
        self.last_mention_id = None
        self.last_dm_id = None
        self.daily_tweet_count = 0
        self.last_tweet_reset = datetime.now()
        self.max_daily_tweets = 10  # Default value, can be overridden
        
        # Initialize threads
        self.posting_thread = None
        self.mention_thread = None
        self.dm_thread = None
        
        logger.info(f"Initialized Twitter agent: {self.character['name']}")
    
    def generate_content(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Generate content using the language model.
        
        Args:
            prompt: Input prompt for content generation
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated content as a string
        """
        try:
            # If in test mode, use mock content generation
            if self.test_mode:
                return self._generate_test_content(prompt)
                
            # Prepare the full prompt with character context
            full_prompt = f"""
            You are {self.character['name']}, {self.character['description']}
            
            Instructions: {self.character['instructions']}
            
            Please respond to the following prompt:
            {prompt}
            """
            
            # Generate content using the model
            hyperbolic_client = self.model["client"]
            model_id = self.model["model_config"]["model_id"]
            
            result = hyperbolic_client.generate_text(
                prompt=full_prompt,
                model_id=model_id,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return result.get("text", "").strip()
        except Exception as e:
            logger.error(f"Failed to generate content: {str(e)}")
            return f"I apologize, but I'm having trouble generating content right now. Please try again later."
    
    def _generate_test_content(self, prompt: str) -> str:
        """
        Generate mock content for testing without Hyperbolic compute.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Mock generated content
        """
        logger.info(f"Test mode: Generating mock content for prompt: {prompt[:50]}...")
        
        import random
        
        # Tweet content options
        tweet_options = [
            f"Bitcoin just broke $75K, setting a new ATH! Institutional inflows continue to drive the market upward. Watch for potential resistance at $80K. #BTC #CryptoMarkets",
            f"Ethereum's Shanghai upgrade has increased staking yields to 7.2% APR. This could attract more validators and strengthen network security. #ETH #Staking #DeFi",
            f"SEC approval of spot ETH ETFs could bring $5-10B in new capital to the market in Q1 2025. Institutional adoption accelerating. #Ethereum #Regulation",
            f"Layer-2 solutions processing 5M+ transactions daily, reducing Ethereum gas fees by 92%. @Arbitrum and @Optimism leading the scaling race. #L2 #Scaling",
            f"DeFi TVL has surpassed $150B, up 65% YTD. Lending protocols seeing renewed interest as yields outpace traditional finance. #DeFi #Yield #Finance"
        ]
        
        # Reply content options
        reply_options = [
            f"Great observation! Bitcoin's 200-day moving average has been a reliable support level during this bull cycle. Currently at $62K, it provides a strong foundation for further upside.",
            f"You raise an important point about regulatory clarity. The new framework proposed by the EU provides a balanced approach that could become a global standard. This would reduce uncertainty for projects and investors alike.",
            f"The correlation between crypto and traditional markets has actually decreased to 0.31 in Q1 2025, down from 0.68 last year. This suggests crypto is maturing as a separate asset class.",
            f"Layer-1 competition is indeed fierce, but Ethereum's developer ecosystem (280K+ active devs) remains 4x larger than its closest competitor. Network effects matter tremendously in this space.",
            f"NFT utility beyond digital art is the real story of 2025. From supply chain verification to identity management, the technology is finding practical applications across industries."
        ]
        
        # DM content options
        dm_options = [
            f"Thanks for your message! Bitcoin's current market structure suggests we're in a mid-cycle accumulation phase similar to Q2 2021. Key levels to watch are $72K (support) and $82K (resistance). If you're considering entry points, dollar-cost averaging has historically outperformed lump-sum investing in similar market conditions. Would you like more specific analysis on any particular assets?",
            f"Great question about DeFi yields! The current spread between lending and borrowing rates on platforms like Aave and Compound (3.2% average) is historically low, suggesting efficient capital allocation. For stablecoin yields specifically, I'd recommend looking at Curve's new gauge system which is offering 8-10% APY with relatively low risk. Always remember to assess smart contract risk before depositing significant funds. Anything else you'd like to know?",
            f"Regarding your question about NFT investments, the market has matured significantly. Focus on projects with: 1) Active developer communities, 2) Clear utility beyond speculation, 3) Sustainable tokenomics. Blue-chip collections have maintained value better than newer launches. The upcoming royalty standardization proposal (EIP-4910) could significantly impact creator economics. Let me know if you need more specific guidance!",
            f"On regulatory developments, the most significant recent change is the new framework from the Financial Stability Board. It classifies tokens into three risk tiers with corresponding compliance requirements. For traders, this means KYC/AML procedures will become more standardized across jurisdictions by Q3 2025. I can share some resources on preparing for these changes if you're interested.",
            f"Regarding your portfolio allocation question, the data suggests a 60/30/10 split between established assets (BTC/ETH), mid-cap alts, and early-stage projects has provided the optimal risk-adjusted returns over the past 3 cycles. Remember that rebalancing quarterly has historically added 2-3% in annual returns. Would you like me to elaborate on specific allocation strategies?"
        ]
        
        # Simple mock responses based on prompt keywords
        if "tweet" in prompt.lower():
            return random.choice(tweet_options)
        
        if "reply" in prompt.lower() or "respond" in prompt.lower() or "mention" in prompt.lower():
            return random.choice(reply_options)
        
        if "direct message" in prompt.lower() or "dm" in prompt.lower():
            return random.choice(dm_options)
        
        if "search" in prompt.lower():
            return f"Interesting perspective on blockchain technology. I believe decentralized finance has tremendous potential to reshape the financial landscape with its open, permissionless architecture and programmable money capabilities."
        
        # Default response
        return f"As {self.character['name']}, I'm here to provide insights on cryptocurrency and blockchain technology. This is a response to your prompt."
    
    def post_scheduled_tweet(self):
        """Post a scheduled tweet based on the agent's character."""
        # Check if we've exceeded the daily tweet limit
        current_time = datetime.now()
        if (current_time - self.last_tweet_reset).days >= 1:
            self.daily_tweet_count = 0
            self.last_tweet_reset = current_time
        
        if self.daily_tweet_count >= self.max_daily_tweets:
            logger.info(f"Daily tweet limit reached ({self.max_daily_tweets}). Skipping scheduled tweet.")
            return
        
        # Generate tweet content
        prompt = """Generate an insightful tweet about cryptocurrency that would rile up investors and enthusiasts.
        
        Choose ONE of these topics:
        1. Recent price movements of major cryptocurrencies (BTC, ETH, etc.)
        2. A notable blockchain technology advancement or update
        3. A regulatory development affecting the crypto market
        4. An institutional adoption trend or news
        5. A DeFi protocol insight or opportunity
        
        Make the tweet truthful, funny, and a little controversial. Include relevant data points or statistics if applicable.
        Add 2-3 relevant hashtags. Keep the entire tweet under 280 characters.
        
        DO NOT use generic statements like "Crypto markets are volatile" - provide specific, timely insights.
        """
        tweet_content = self.generate_content(prompt, max_tokens=100)
        
        # Ensure the tweet is within Twitter's character limit
        if len(tweet_content) > 280:
            tweet_content = tweet_content[:277] + "..."
        
        # Post the tweet
        result = post_tweet(self.twitter_client, tweet_content)
        
        if result["success"]:
            self.daily_tweet_count += 1
            logger.info(f"Posted scheduled tweet: {tweet_content}")
        else:
            logger.error(f"Failed to post scheduled tweet: {result.get('error')}")
    
    def handle_mentions(self):
        """Handle mentions and reply to them."""
        try:
            # Get recent mentions
            result = get_mentions(
                self.twitter_client, 
                since_id=self.last_mention_id
            )
            
            if not result["success"]:
                logger.error(f"Failed to retrieve mentions: {result.get('error')}")
                return
            
            mentions = result.get("mentions", [])
            if not mentions:
                logger.info("No new mentions found")
                return
            
            # Update the last mention ID
            self.last_mention_id = mentions[0].id
            
            # Process mentions in reverse order (oldest first)
            for mention in reversed(mentions):
                # Extract the tweet text and remove the agent's username
                tweet_text = mention.text
                
                # Generate a response
                prompt = f"""Someone tweeted at you: '{tweet_text}'
                
                Respond with a helpful, informative reply about cryptocurrency or blockchain technology that directly addresses their query or comment.
                
                Your response should:
                1. Be knowledgeable and accurate
                2. Provide specific information, not generic advice
                3. Include relevant facts or data points when appropriate
                4. Be controversial but helpful
                5. Stay under 280 characters
                
                If they're asking a question, answer it directly. If they're sharing an opinion, engage thoughtfully with their perspective.
                """
                response_content = self.generate_content(prompt, max_tokens=200)
                
                # Ensure the response is within Twitter's character limit
                if len(response_content) > 280:
                    response_content = response_content[:277] + "..."
                
                # Reply to the mention
                reply_result = reply_to_tweet(
                    self.twitter_client,
                    content=response_content,
                    tweet_id=mention.id
                )
                
                if reply_result["success"]:
                    logger.info(f"Replied to mention {mention.id}: {response_content}")
                else:
                    logger.error(f"Failed to reply to mention {mention.id}: {reply_result.get('error')}")
                
                # Add a small delay to avoid rate limits
                time.sleep(2)
        except Exception as e:
            logger.error(f"Error handling mentions: {str(e)}")
    
    def handle_direct_messages(self):
        """Handle direct messages and respond to them."""
        try:
            # Get recent direct messages
            result = get_direct_messages(
                self.twitter_client,
                since_id=self.last_dm_id
            )
            
            if not result["success"]:
                logger.error(f"Failed to retrieve direct messages: {result.get('error')}")
                return
            
            dms = result.get("direct_messages", [])
            if not dms:
                logger.info("No new direct messages found")
                return
            
            # Update the last DM ID
            self.last_dm_id = dms[0].id
            
            # Process DMs in reverse order (oldest first)
            for dm in reversed(dms):
                # Skip messages sent by the bot itself
                if hasattr(dm, 'sender_id'):
                    sender_id = dm.sender_id
                elif hasattr(dm, 'message_create'):
                    sender_id = dm.message_create['sender_id']
                else:
                    logger.warning(f"Could not determine sender for DM: {dm.id}")
                    continue
                
                # Get the authenticated user's ID
                user_id = None
                if self.twitter_client["v2_client"]:
                    user_id = self.twitter_client["v2_client"].get_me().data.id
                elif self.twitter_client["v1_api"]:
                    user_id = str(self.twitter_client["v1_api"].verify_credentials().id)
                
                # Skip if the message was sent by the bot itself
                if user_id and str(sender_id) == str(user_id):
                    continue
                
                # Extract the message text
                if hasattr(dm, 'text'):
                    message_text = dm.text
                elif hasattr(dm, 'message_create'):
                    message_text = dm.message_create['message_data']['text']
                else:
                    logger.warning(f"Could not extract text from DM: {dm.id}")
                    continue
                
                # Generate a response
                prompt = f"""Someone sent you a direct message: '{message_text}'
                
                Respond with a personalized, helpful reply about cryptocurrency or blockchain technology that directly addresses their message.
                
                Your response should:
                1. Be knowledgeable and accurate
                2. Provide specific, actionable information
                3. Include relevant facts, data points, or resources when appropriate
                4. Be friendly, conversational, and engaging
                5. Offer to help further if they have more questions
                
                Since this is a private message, you can provide more detailed information than in a public tweet.
                If they're asking a question, answer it thoroughly. If they're sharing thoughts, engage thoughtfully with their perspective.
                """
                response_content = self.generate_content(prompt, max_tokens=500)
                
                # Send the response
                response_result = send_direct_message(
                    self.twitter_client,
                    recipient_id=sender_id,
                    text=response_content
                )
                
                if response_result["success"]:
                    logger.info(f"Replied to DM from {sender_id}: {response_content[:50]}...")
                else:
                    logger.error(f"Failed to reply to DM from {sender_id}: {response_result.get('error')}")
                
                # Add a small delay to avoid rate limits
                time.sleep(2)
        except Exception as e:
            logger.error(f"Error handling direct messages: {str(e)}")
    
    def posting_loop(self):
        """Main loop for posting scheduled tweets."""
        logger.info("Starting posting loop")
        
        try:
            # Post a tweet immediately when starting
            logger.info("Posting initial tweet...")
            self.post_scheduled_tweet()
        except Exception as e:
            logger.error(f"Error posting initial tweet: {str(e)}")
        
        while self.running:
            try:
                # Sleep until the next posting interval
                time.sleep(self.posting_interval)
                self.post_scheduled_tweet()
            except Exception as e:
                logger.error(f"Error in posting loop: {str(e)}")
    
    def mention_loop(self):
        """Main loop for checking and responding to mentions."""
        logger.info("Starting mention checking loop")
        
        while self.running:
            try:
                self.handle_mentions()
            except Exception as e:
                logger.error(f"Error in mention loop: {str(e)}")
            
            # Sleep until the next mention check interval
            time.sleep(self.mention_check_interval)
    
    def dm_loop(self):
        """Main loop for checking and responding to direct messages."""
        logger.info("Starting direct message checking loop")
        
        while self.running:
            try:
                self.handle_direct_messages()
            except Exception as e:
                logger.error(f"Error in DM loop: {str(e)}")
            
            # Sleep until the next DM check interval
            time.sleep(self.dm_check_interval)
    
    def start(self, mode: str = "autonomous", posting_interval: int = 7200,
             mention_check_interval: int = 300, dm_check_interval: int = 300,
             max_daily_tweets: int = 10):
        """
        Start the Twitter agent.
        
        Args:
            mode: Operation mode ("autonomous" or "manual")
            posting_interval: Interval between scheduled posts in seconds (default: 7200 - 2 hours)
            mention_check_interval: Interval between mention checks in seconds
            dm_check_interval: Interval between direct message checks in seconds
            max_daily_tweets: Maximum number of tweets to post per day
        """
        if self.running:
            logger.warning("Agent is already running")
            return
        
        self.running = True
        self.posting_interval = posting_interval
        self.mention_check_interval = mention_check_interval
        self.dm_check_interval = dm_check_interval
        self.max_daily_tweets = max_daily_tweets
        
        logger.info(f"Starting Twitter agent in {mode} mode")
        logger.info(f"Posting interval: {posting_interval} seconds (every {posting_interval/3600:.1f} hours)")
        logger.info(f"Mention check interval: {mention_check_interval} seconds")
        logger.info(f"DM check interval: {dm_check_interval} seconds")
        
        if mode == "autonomous":
            # Start the posting thread
            self.posting_thread = threading.Thread(target=self.posting_loop)
            self.posting_thread.daemon = True
            self.posting_thread.start()
            
            # Start the mention thread
            self.mention_thread = threading.Thread(target=self.mention_loop)
            self.mention_thread.daemon = True
            self.mention_thread.start()
            
            # Start the DM thread
            self.dm_thread = threading.Thread(target=self.dm_loop)
            self.dm_thread.daemon = True
            self.dm_thread.start()
        
        logger.info("Agent successfully started")
    
    def stop(self):
        """Stop the Twitter agent."""
        if not self.running:
            logger.warning("Agent is not running")
            return
        
        logger.info("Stopping Twitter agent")
        self.running = False
        
        # Wait for threads to terminate
        if self.posting_thread and self.posting_thread.is_alive():
            self.posting_thread.join(timeout=5)
        
        if self.mention_thread and self.mention_thread.is_alive():
            self.mention_thread.join(timeout=5)
        
        if self.dm_thread and self.dm_thread.is_alive():
            self.dm_thread.join(timeout=5)
        
        logger.info("Agent successfully stopped")
    
    def post_single_tweet(self, content: str) -> Dict[str, Any]:
        """
        Post a single tweet with the given content.
        
        Args:
            content: Tweet content
            
        Returns:
            Result dictionary with success status and tweet data or error
        """
        try:
            # Ensure the tweet is within Twitter's character limit
            if len(content) > 280:
                content = content[:277] + "..."
            
            # Post the tweet
            result = post_tweet(self.twitter_client, content)
            
            if result["success"]:
                logger.info(f"Posted single tweet: {content}")
            else:
                logger.error(f"Failed to post single tweet: {result.get('error')}")
            
            return result
        except Exception as e:
            logger.error(f"Error posting single tweet: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def reply_to_single_tweet(self, tweet_id: str, content: str) -> Dict[str, Any]:
        """
        Reply to a single tweet.
        
        Args:
            tweet_id: ID of the tweet to reply to
            content: Content of the reply
            
        Returns:
            Dictionary containing the result of the reply
        """
        return reply_to_tweet(self.twitter_client, content, tweet_id)
    
    def send_single_dm(self, recipient_id: str, content: str) -> Dict[str, Any]:
        """
        Send a direct message to a specific user.
        
        Args:
            recipient_id: ID of the user to send the message to
            content: Content of the direct message
            
        Returns:
            Dictionary containing the result of the message
        """
        return send_direct_message(self.twitter_client, recipient_id, content)
    
    def search_and_engage(self, query: str, max_results: int = 10, 
                         action: str = "reply") -> List[Dict[str, Any]]:
        """
        Search for tweets and engage with them.
        
        Args:
            query: Search query string
            max_results: Maximum number of tweets to engage with
            action: Engagement action ("reply", "retweet", "like", or "all")
            
        Returns:
            List of dictionaries containing the results of the engagements
        """
        # Search for tweets
        search_result = search_tweets(self.twitter_client, query, max_results)
        
        if not search_result["success"]:
            logger.error(f"Failed to search tweets: {search_result.get('error')}")
            return []
        
        tweets = search_result.get("tweets", [])
        if not tweets:
            logger.info(f"No tweets found for query: {query}")
            return []
        
        results = []
        
        for tweet in tweets:
            engagement_result = {"tweet_id": tweet.id, "actions": []}
            
            # Perform the requested actions
            if action in ["reply", "all"]:
                prompt = f"Someone tweeted: '{tweet.text}'. Generate a helpful, concise response about cryptocurrency or blockchain technology that addresses their tweet."
                response_content = self.generate_content(prompt, max_tokens=200)
                
                # Ensure the response is within Twitter's character limit
                if len(response_content) > 280:
                    response_content = response_content[:277] + "..."
                
                reply_result = reply_to_tweet(
                    self.twitter_client,
                    content=response_content,
                    tweet_id=tweet.id
                )
                
                engagement_result["actions"].append({
                    "type": "reply",
                    "success": reply_result["success"],
                    "content": response_content if reply_result["success"] else None,
                    "error": reply_result.get("error")
                })
            
            if action in ["retweet", "all"]:
                retweet_result = retweet(self.twitter_client, tweet.id)
                
                engagement_result["actions"].append({
                    "type": "retweet",
                    "success": retweet_result["success"],
                    "error": retweet_result.get("error")
                })
            
            if action in ["like", "all"]:
                like_result = like_tweet(self.twitter_client, tweet.id)
                
                engagement_result["actions"].append({
                    "type": "like",
                    "success": like_result["success"],
                    "error": like_result.get("error")
                })
            
            results.append(engagement_result)
            
            # Add a small delay to avoid rate limits
            time.sleep(2)
        
        return results
    
    def get_agent_metrics(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.
        
        Returns:
            Dictionary containing agent metrics
        """
        # If in test mode, return mock metrics
        if self.test_mode:
            return {
                "agent_name": self.character["name"],
                "daily_tweet_count": self.daily_tweet_count,
                "max_daily_tweets": self.max_daily_tweets,
                "uptime_seconds": (datetime.now() - self.last_tweet_reset).total_seconds(),
                "test_mode": True
            }
            
        # Get GPU status
        hyperbolic_client = self.model["client"]
        gpu_status = hyperbolic_client.check_gpu_status()
        
        # Get billing information
        billing = hyperbolic_client.query_billing_history()
        
        # Calculate agent uptime
        uptime = (datetime.now() - self.last_tweet_reset).total_seconds()
        
        return {
            "agent_name": self.character["name"],
            "daily_tweet_count": self.daily_tweet_count,
            "max_daily_tweets": self.max_daily_tweets,
            "uptime_seconds": uptime,
            "gpu_status": gpu_status,
            "billing": billing
        }
    
    def optimize_agent_costs(self) -> Dict[str, Any]:
        """
        Optimize agent costs by analyzing GPU usage.
        
        Returns:
            Dictionary containing cost optimization recommendations
        """
        if self.test_mode:
            logger.info("Cost optimization not available in test mode")
            return {"test_mode": True, "message": "Cost optimization not available in test mode"}
            
        return optimize_costs()
    
    def __del__(self):
        """Cleanup when the agent is destroyed."""
        if self.running:
            self.stop()
        
        # Release GPU resources if not in test mode
        if not self.test_mode:
            try:
                hyperbolic_client = self.model["client"]
                hyperbolic_client.release_gpu()
                logger.info("Released GPU resources")
            except Exception as e:
                logger.error(f"Error releasing GPU resources: {str(e)}") 