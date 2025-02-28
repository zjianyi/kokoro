"""
Hyperbolic compute integration for the Twitter agent.
"""
import os
import json
import time
import logging
import requests
from typing import Dict, Any, Optional, Tuple, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HyperbolicClient:
    """Client for interacting with Hyperbolic's GPU marketplace."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.hyperbolic.xyz"):
        """
        Initialize the Hyperbolic client.
        
        Args:
            api_key: Hyperbolic API key
            base_url: Base URL for Hyperbolic API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
        self.gpu_id = None
        
        logger.info("Initialized Hyperbolic client")
    
    def rent_gpu(self, model_id: str, max_price: Optional[float] = 10) -> Dict[str, Any]:
        """
        Rent a GPU from the marketplace.
        
        Args:
            model_id: ID of the model to run
            max_price: Maximum price willing to pay per hour
            
        Returns:
            Dictionary containing GPU information
        """
        try:
            url = f"{self.base_url}/v1/gpus/rent"
            
            payload = {
                "model_id": model_id
            }
            
            if max_price is not None:
                payload["max_price"] = max_price
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.gpu_id = data.get("gpu_id")
            
            logger.info(f"Successfully rented GPU: {self.gpu_id}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to rent GPU: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def release_gpu(self) -> Dict[str, Any]:
        """
        Release the rented GPU.
        
        Returns:
            Dictionary containing release confirmation
        """
        if not self.gpu_id:
            logger.warning("No GPU to release")
            return {"success": False, "error": "No GPU to release"}
        
        try:
            url = f"{self.base_url}/v1/gpus/{self.gpu_id}/release"
            
            response = self.session.post(url)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully released GPU: {self.gpu_id}")
            
            self.gpu_id = None
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to release GPU: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def check_gpu_status(self) -> Dict[str, Any]:
        """
        Check the status of the rented GPU.
        
        Returns:
            Dictionary containing GPU status
        """
        if not self.gpu_id:
            logger.warning("No GPU to check status")
            return {"success": False, "error": "No GPU to check status"}
        
        try:
            url = f"{self.base_url}/v1/gpus/{self.gpu_id}"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"GPU status: {data.get('status')}")
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check GPU status: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def generate_text(self, prompt: str, model_id: str, 
                     max_tokens: int = 1000, temperature: float = 0.7,
                     top_p: float = 0.9, top_k: int = 40) -> Dict[str, Any]:
        """
        Generate text using the rented GPU.
        
        Args:
            prompt: Input prompt for text generation
            model_id: ID of the model to use
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            
        Returns:
            Dictionary containing generated text
        """
        if not self.gpu_id:
            logger.warning("No GPU for text generation, attempting to rent one")
            self.rent_gpu(model_id)
        
        try:
            url = f"{self.base_url}/v1/generate"
            
            payload = {
                "prompt": prompt,
                "model_id": model_id,
                "gpu_id": self.gpu_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k
            }
            
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully generated text ({len(data.get('text', ''))} chars)")
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate text: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
    
    def query_billing_history(self) -> Dict[str, Any]:
        """
        Query billing history.
        
        Returns:
            Dictionary containing billing history
        """
        try:
            url = f"{self.base_url}/v1/billing/history"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            logger.info("Successfully retrieved billing history")
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to query billing history: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

def setup_hyperbolic_compute(api_key: str) -> HyperbolicClient:
    """
    Set up Hyperbolic compute resources.
    
    Args:
        api_key: Hyperbolic API key
        
    Returns:
        Initialized Hyperbolic client
    """
    try:
        # Initialize Hyperbolic client
        client = HyperbolicClient(api_key)
        logger.info("Hyperbolic client initialized")
        
        return client
    except Exception as e:
        logger.error(f"Failed to set up Hyperbolic compute: {str(e)}")
        raise

def initialize_hyperbolic_model(client: HyperbolicClient, model_id: str, 
                              max_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Initialize a language model on Hyperbolic.
    
    Args:
        client: Initialized Hyperbolic client
        model_id: ID of the model to initialize
        max_price: Maximum price willing to pay per hour
        
    Returns:
        Dictionary containing model configuration and client
    """
    try:
        # Rent a GPU for the model
        gpu_info = client.rent_gpu(model_id, max_price)
        
        # Wait for GPU to be ready
        status = "pending"
        max_retries = 10
        retry_count = 0
        
        while status == "pending" and retry_count < max_retries:
            gpu_status = client.check_gpu_status()
            status = gpu_status.get("status", "pending")
            
            if status == "ready":
                logger.info("GPU is ready for inference")
                break
            
            logger.info(f"Waiting for GPU to be ready (status: {status})...")
            time.sleep(5)
            retry_count += 1
        
        if status != "ready":
            logger.warning(f"GPU not ready after {max_retries} retries")
        
        # Return model configuration
        return {
            "client": client,
            "model_config": {
                "model_id": model_id,
                "gpu_id": client.gpu_id,
                "max_price": max_price
            }
        }
    except Exception as e:
        logger.error(f"Failed to initialize Hyperbolic model: {str(e)}")
        raise

def optimize_costs() -> Dict[str, Any]:
    """
    Analyze and optimize GPU costs.
    
    Returns:
        Dictionary containing cost optimization recommendations
    """
    try:
        # This is a placeholder for actual cost optimization logic
        # In a real implementation, this would analyze usage patterns and suggest optimizations
        
        recommendations = {
            "current_usage": {
                "hours_per_day": 24,
                "cost_per_hour": 0.50,
                "daily_cost": 12.00
            },
            "recommendations": [
                {
                    "type": "schedule_optimization",
                    "description": "Schedule GPU usage during off-peak hours",
                    "estimated_savings": "20%"
                },
                {
                    "type": "model_optimization",
                    "description": "Consider using a smaller model for simpler tasks",
                    "estimated_savings": "30%"
                },
                {
                    "type": "batch_processing",
                    "description": "Batch similar requests together",
                    "estimated_savings": "15%"
                }
            ]
        }
        
        logger.info("Generated cost optimization recommendations")
        return recommendations
    except Exception as e:
        logger.error(f"Failed to optimize costs: {str(e)}")
        return {
            "error": str(e),
            "recommendations": []
        } 