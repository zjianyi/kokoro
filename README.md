# Twitter Agent Using Hyperbolic

This project implements a Twitter agent using Hyperbolic's decentralized GPU marketplace and agent framework. The agent can post tweets, respond to mentions, and perform various Twitter actions while leveraging cost-effective GPU resources.

## Setup Instructions

### Prerequisites

- Python 3.12
- Twitter API credentials
- Hyperbolic API key (obtain from app.hyperbolic.xyz)

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd twitter-hyperbolic-agent
```

2. Create a virtual environment:
```bash
python3.12 -m venv hyperbolic-agent-env
source hyperbolic-agent-env/bin/activate  # On Windows: hyperbolic-agent-env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
```

5. Configure environment variables:
```bash
cp .env.example .env
```
Then edit the `.env` file with your API keys and configuration.

### Configuration

Edit the `character.json` file to customize your agent's personality, capabilities, and behavior.

### Running the Agent

```bash
python main.py
```

## Features

- Twitter posting, replying, and retweeting capabilities
- Cost-effective GPU usage through Hyperbolic's marketplace
- Customizable agent personality
- Monitoring and cost optimization tools

## Project Structure

- `main.py`: Entry point for the application
- `twitter_agent.py`: Core Twitter agent implementation
- `custom_twitter_actions.py`: Twitter API interaction functions
- `hyperbolic_compute.py`: Hyperbolic GPU marketplace integration
- `character.json`: Agent personality configuration
- `.env`: Environment variables and API keys
- `.env.example`: Example environment file template 