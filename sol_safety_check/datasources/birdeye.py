"""Birdeye API client for fetching token information and market data."""

import asyncio
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..utils import get_env_var, make_http_request

logger = logging.getLogger(__name__)


class BirdeyeClient:
    """Client for interacting with Birdeye API."""
    
    BASE_URL = "https://public-api.birdeye.so"
    
    def __init__(self):
        """Initialize Birdeye client with API key if available."""
        self.api_key = get_env_var("BIRDEYE_API_KEY")
        self.headers = {"x-chain": "solana"}
        if self.api_key:
            self.headers["X-API-KEY"] = self.api_key
            logger.info("Birdeye API key found, using authenticated requests")
        else:
            logger.warning("No Birdeye API key found, using public endpoints only")
    
    async def get_token_overview(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token overview information from Birdeye using V3 API.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with token overview or None if failed
        """
        url = f"{self.BASE_URL}/defi/v3/token/overview"
        params = {"address": mint_address}
        
        success, data, error = await make_http_request(
            url, 
            params=params, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch token overview from Birdeye: {error}")
            return None
        
        return data.get("data", {})
    
    async def get_token_price(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get current token price from Birdeye using V3 API.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with price information or None if failed
        """
        url = f"{self.BASE_URL}/defi/v3/price/stats/single"
        params = {"address": mint_address}
        
        success, data, error = await make_http_request(
            url, 
            params=params, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch token price from Birdeye: {error}")
            return None
        
        return data.get("data", {})
    
    async def get_holder_stats(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get holder statistics from Birdeye using V3 API.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with holder stats or None if failed
        """
        url = f"{self.BASE_URL}/defi/v3/token/holder"
        params = {"address": mint_address}
        
        success, data, error = await make_http_request(
            url, 
            params=params, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch holder stats from Birdeye: {error}")
            return None
        
        return data.get("data", {})
    
    async def get_pools(self, mint_address: str) -> List[Dict[str, Any]]:
        """
        Get trading pools for a token from Birdeye using V3 API.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            List of pool dictionaries
        """
        url = f"{self.BASE_URL}/defi/v3/pair/overview/multiple"
        params = {"address": mint_address}
        
        success, data, error = await make_http_request(
            url, 
            params=params, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch pools from Birdeye: {error}")
            return []
        
        return data.get("data", {}).get("items", [])
    
    async def get_ohlcv(self, mint_address: str, timeframe: str = "1h") -> Optional[Dict[str, Any]]:
        """
        Get OHLCV data from Birdeye using V3 API.
        
        Args:
            mint_address: The token mint address
            timeframe: Timeframe for OHLCV data (1s, 15s, 30s, 1m, 5m, 15m, 1h, 4h, 1d)
            
        Returns:
            Dictionary with OHLCV data or None if failed
        """
        url = f"{self.BASE_URL}/defi/v3/ohlcv"
        params = {
            "address": mint_address,
            "type": timeframe,
        }
        
        success, data, error = await make_http_request(
            url, 
            params=params, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch OHLCV from Birdeye: {error}")
            return None
        
        return data.get("data", {})
    
    async def get_token_metadata(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token metadata from Birdeye using V3 API.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with token metadata or None if failed
        """
        url = f"{self.BASE_URL}/defi/v3/token/meta-data/single"
        params = {"address": mint_address}
        
        success, data, error = await make_http_request(
            url, 
            params=params, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch token metadata from Birdeye: {error}")
            return None
        
        return data.get("data", {})
    
    async def get_token_market_data(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token market data from Birdeye using V3 API.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with market data or None if failed
        """
        url = f"{self.BASE_URL}/defi/v3/token/market-data"
        params = {"address": mint_address}
        
        success, data, error = await make_http_request(
            url, 
            params=params, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch market data from Birdeye: {error}")
            return None
        
        return data.get("data", {})
    
    async def get_token_trade_data(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token trade data from Birdeye using V3 API.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with trade data or None if failed
        """
        url = f"{self.BASE_URL}/defi/v3/token/trade-data/single"
        params = {"address": mint_address}
        
        success, data, error = await make_http_request(
            url, 
            params=params, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch trade data from Birdeye: {error}")
            return None
        
        return data.get("data", {})
    
    async def get_token_security(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token security information from Birdeye.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with security information or None if failed
        """
        url = f"{self.BASE_URL}/defi/token_security"
        params = {"address": mint_address}
        
        success, data, error = await make_http_request(
            url, 
            params=params, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch security info from Birdeye: {error}")
            return None
        
        return data.get("data", {})
    
    async def get_token_creation_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token creation information from Birdeye.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with creation info or None if failed
        """
        url = f"{self.BASE_URL}/defi/token_creation_info"
        params = {"address": mint_address}
        
        success, data, error = await make_http_request(
            url, 
            params=params, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch creation info from Birdeye: {error}")
            return None
        
        return data.get("data", {})
    
    async def get_token_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive token information from Birdeye using available endpoints.
        Uses sequential requests to respect rate limits.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with comprehensive token information
        """
        # Use sequential requests to respect 1 rps rate limit
        overview = await self.get_token_overview(mint_address)
        await asyncio.sleep(1)  # Respect rate limit
        
        price = await self.get_token_price(mint_address)
        await asyncio.sleep(1)  # Respect rate limit
        
        pools = await self.get_pools(mint_address)
        await asyncio.sleep(1)  # Respect rate limit
        
        # Only try a few more endpoints to avoid rate limiting
        metadata = await self.get_token_metadata(mint_address)
        await asyncio.sleep(1)  # Respect rate limit
        
        # Combine data
        result = {
            "address": mint_address,
            "overview": overview or {},
            "price": price or {},
            "pools": pools or [],
            "metadata": metadata or {},
        }
        
        return result
