# Twitter Agent Usage Guide

This guide provides examples of how to use the Twitter agent with Hyperbolic's GPU marketplace.

## Basic Usage

To start the Twitter agent in autonomous mode with default settings:

```bash
python main.py
```

This will:
- Start the agent in autonomous mode
- Post tweets every hour (3600 seconds)
- Check for mentions every 5 minutes (300 seconds)
- Limit to 10 tweets per day

## Command Line Options

The agent supports various command line options to customize its behavior:

### Changing Operation Mode

```bash
# Run in autonomous mode (default)
python main.py --mode autonomous

# Run in manual mode (no automatic posting or mention checking)
python main.py --mode manual
```

### Adjusting Posting Frequency

```bash
# Post every 30 minutes
python main.py --posting-interval 1800

# Post every 2 hours
python main.py --posting-interval 7200
```

### Adjusting Mention Checking Frequency

```bash
# Check mentions every minute
python main.py --mention-interval 60

# Check mentions every 10 minutes
python main.py --mention-interval 600
```

### Setting Daily Tweet Limit

```bash
# Limit to 5 tweets per day
python main.py --max-tweets 5

# Limit to 20 tweets per day
python main.py --max-tweets 20
```

## One-off Commands

The agent also supports one-off commands that execute a single action and then exit:

### Posting a Single Tweet

```bash
python main.py --post-tweet "Bitcoin has reached a new all-time high today! #crypto #bitcoin"
```

### Searching and Engaging with Tweets

```bash
# Search for tweets about Ethereum and reply to them
python main.py --search-engage "ethereum blockchain" --engagement-action reply

# Search for tweets about NFTs and retweet them
python main.py --search-engage "NFT marketplace" --engagement-action retweet

# Search for tweets about DeFi and like them
python main.py --search-engage "DeFi protocol" --engagement-action like

# Search for tweets about Web3 and perform all engagement actions
python main.py --search-engage "Web3 development" --engagement-action all
```

### Cost Optimization

```bash
# Run cost optimization analysis
python main.py --optimize-costs
```

## Combining Options

You can combine multiple options to customize the agent's behavior:

```bash
# Run in autonomous mode, post every 2 hours, check mentions every 2 minutes, limit to 8 tweets per day
python main.py --mode autonomous --posting-interval 7200 --mention-interval 120 --max-tweets 8
```

## Environment Variables

The agent requires several environment variables to be set in the `.env` file:

```
# Hyperbolic API Key
HYPERBOLIC_API_KEY=your_hyperbolic_api_key
HYPERBOLIC_MODEL=llama3b  # Choose your preferred model

# Twitter/X API Credentials
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_token_secret
```

## Agent Personality

The agent's personality is defined in the `character.json` file. You can customize this file to change the agent's behavior, tone, and capabilities.

## Logging

The agent logs its activities to both the console and a file named `twitter_agent.log`. You can check this file for detailed information about the agent's operations.

## Stopping the Agent

To stop the agent, press `Ctrl+C` in the terminal where it's running. The agent will gracefully shut down, releasing any GPU resources it has rented. 