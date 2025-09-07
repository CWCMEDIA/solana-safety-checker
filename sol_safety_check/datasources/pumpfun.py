"""Pump.fun intelligence client for fetching token creation and migration data."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from ..utils import get_env_var, make_http_request

logger = logging.getLogger(__name__)


class PumpFunClient:
    """Client for interacting with Pump.fun related APIs."""
    
    def __init__(self):
        """Initialize Pump.fun client with API keys if available."""
        self.moralis_api_key = get_env_var("MORALIS_API_KEY")
        self.bitquery_api_key = get_env_var("BITQUERY_API_KEY")
        
        if self.moralis_api_key:
            logger.info("Moralis API key found, using for Pump.fun analysis")
        elif self.bitquery_api_key:
            logger.info("Bitquery API key found, using for Pump.fun analysis")
        else:
            logger.warning("No Pump.fun API keys found, skipping Pump.fun analysis")
    
    async def get_token_info_moralis(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token information using Moralis API.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with token information or None if failed
        """
        if not self.moralis_api_key:
            return None
        
        url = f"https://solana-gateway.moralis.io/token/{mint_address}/metadata"
        headers = {
            "X-API-Key": self.moralis_api_key,
            "Content-Type": "application/json",
        }
        
        success, data, error = await make_http_request(
            url, 
            headers=headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch token info from Moralis: {error}")
            return None
        
        return data
    
    async def get_token_holders_moralis(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token holders using Moralis API.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with holder information or None if failed
        """
        if not self.moralis_api_key:
            return None
        
        url = f"https://solana-gateway.moralis.io/token/{mint_address}/holders"
        headers = {
            "X-API-Key": self.moralis_api_key,
            "Content-Type": "application/json",
        }
        
        success, data, error = await make_http_request(
            url, 
            headers=headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch token holders from Moralis: {error}")
            return None
        
        return data
    
    async def get_token_info_bitquery(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token information using Bitquery API.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with token information or None if failed
        """
        if not self.bitquery_api_key:
            return None
        
        url = "https://graphql.bitquery.io"
        headers = {
            "X-API-KEY": self.bitquery_api_key,
            "Content-Type": "application/json",
        }
        
        # GraphQL query for Solana token information
        query = """
        query GetTokenInfo($mint: String!) {
          solana(network: solana) {
            tokenMints(
              mint: {is: $mint}
            ) {
              mint
              decimals
              supply
              tokenMintInfo {
                name
                symbol
              }
            }
          }
        }
        """
        
        json_data = {
            "query": query,
            "variables": {"mint": mint_address}
        }
        
        success, data, error = await make_http_request(
            url, 
            method="POST",
            headers=headers,
            json_data=json_data
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch token info from Bitquery: {error}")
            return None
        
        return data
    
    async def get_pump_fun_creation_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get Pump.fun creation information for a token.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with creation information or None if failed
        """
        # This is a placeholder implementation
        # In practice, you would need to:
        # 1. Check if the token is actually from Pump.fun
        # 2. Query Pump.fun's API or use on-chain data
        # 3. Parse creation transactions and metadata
        
        # For now, we'll return basic info if it looks like a Pump.fun token
        if mint_address.endswith("pump") or len(mint_address) == 44:
            return {
                "is_pump_fun_token": True,
                "creation_time": None,  # Would need to query actual data
                "dev_wallet": None,     # Would need to query actual data
                "migration_status": "unknown",
                "dev_holdings_percentage": None,
            }
        
        return None
    
    async def get_token_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive token information from available Pump.fun sources.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with comprehensive token information
        """
        # Try Moralis first if available
        moralis_info = None
        if self.moralis_api_key:
            try:
                moralis_info = await self.get_token_info_moralis(mint_address)
            except Exception as e:
                logger.warning(f"Error fetching from Moralis: {e}")
        
        # Try Bitquery if Moralis failed or not available
        bitquery_info = None
        if not moralis_info and self.bitquery_api_key:
            try:
                bitquery_info = await self.get_token_info_bitquery(mint_address)
            except Exception as e:
                logger.warning(f"Error fetching from Bitquery: {e}")
        
        # Get Pump.fun specific info
        pump_fun_info = await self.get_pump_fun_creation_info(mint_address)
        
        # Combine results
        result = {
            "address": mint_address,
            "moralis_info": moralis_info,
            "bitquery_info": bitquery_info,
            "pump_fun_info": pump_fun_info,
        }
        
        return result
    
    def is_pump_fun_token(self, mint_address: str) -> bool:
        """
        Check if a token is likely from Pump.fun.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            True if likely from Pump.fun, False otherwise
        """
        # This is a heuristic - in practice, you'd check metadata or use API calls
        return mint_address.endswith("pump") or len(mint_address) == 44
    
    def parse_creation_time(self, data: Dict[str, Any]) -> Optional[datetime]:
        """
        Parse creation time from API data.
        
        Args:
            data: API response data
            
        Returns:
            Parsed datetime or None
        """
        # Try various possible fields for creation time
        time_fields = ["created_at", "createdAt", "creation_time", "creationTime", "timestamp"]
        
        for field in time_fields:
            if field in data and data[field]:
                try:
                    # Handle different timestamp formats
                    timestamp = data[field]
                    if isinstance(timestamp, (int, float)):
                        return datetime.fromtimestamp(timestamp)
                    elif isinstance(timestamp, str):
                        # Try to parse ISO format
                        return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except (ValueError, TypeError, OSError):
                    continue
        
        return None
    
    def parse_dev_wallet(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Parse dev wallet address from API data.
        
        Args:
            data: API response data
            
        Returns:
            Dev wallet address or None
        """
        # Try various possible fields for dev wallet
        wallet_fields = ["dev_wallet", "devWallet", "creator", "creator_wallet", "creatorWallet"]
        
        for field in wallet_fields:
            if field in data and data[field]:
                return str(data[field])
        
        return None
