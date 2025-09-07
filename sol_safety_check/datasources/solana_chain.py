"""Solana chain client for fetching on-chain token information."""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..utils import get_env_var, make_http_request

logger = logging.getLogger(__name__)


class SolanaChainClient:
    """Client for interacting with Solana RPC endpoints."""
    
    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize Solana chain client.
        
        Args:
            rpc_url: Custom RPC URL, defaults to SOLANA_RPC_URL env var
        """
        self.rpc_url = rpc_url or get_env_var("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        logger.info(f"Using Solana RPC: {self.rpc_url}")
    
    async def _make_rpc_request(self, method: str, params: List[Any]) -> Optional[Dict[str, Any]]:
        """
        Make a JSON-RPC request to Solana.
        
        Args:
            method: RPC method name
            params: RPC parameters
            
        Returns:
            RPC response data or None if failed
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        success, data, error = await make_http_request(
            self.rpc_url,
            method="POST",
            json_data=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if not success or not data:
            logger.warning(f"RPC request failed: {error}")
            return None
        
        if "error" in data:
            logger.warning(f"RPC error: {data['error']}")
            return None
        
        return data.get("result")
    
    async def get_mint_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get mint information for a token.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with mint information or None if failed
        """
        result = await self._make_rpc_request(
            "getAccountInfo",
            [mint_address, {"encoding": "base64"}]
        )
        
        if not result or not result.get("value"):
            logger.warning(f"No account info found for mint: {mint_address}")
            return None
        
        account_data = result["value"]
        
        # Parse account data (simplified - in practice you'd need to decode the binary data)
        return {
            "address": mint_address,
            "owner": account_data.get("owner"),
            "executable": account_data.get("executable", False),
            "lamports": account_data.get("lamports", 0),
            "data": account_data.get("data"),
        }
    
    async def get_token_supply(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token supply information.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with supply information or None if failed
        """
        result = await self._make_rpc_request(
            "getTokenSupply",
            [mint_address]
        )
        
        if not result:
            logger.warning(f"Failed to get token supply for: {mint_address}")
            return None
        
        return result
    
    async def get_token_accounts_by_mint(self, mint_address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get token accounts for a mint.
        
        Args:
            mint_address: The token mint address
            limit: Maximum number of accounts to return
            
        Returns:
            List of token account information
        """
        result = await self._make_rpc_request(
            "getTokenAccountsByMint",
            [mint_address, {"encoding": "jsonParsed"}]
        )
        
        if not result or not result.get("value"):
            logger.warning(f"No token accounts found for mint: {mint_address}")
            return []
        
        accounts = result["value"][:limit]  # Limit results
        
        # Parse account data
        parsed_accounts = []
        for account in accounts:
            try:
                account_info = account.get("account", {}).get("data", {}).get("parsed", {})
                if account_info.get("type") == "account":
                    info = account_info.get("info", {})
                    parsed_accounts.append({
                        "address": account.get("pubkey"),
                        "owner": info.get("owner"),
                        "mint": info.get("mint"),
                        "balance": info.get("tokenAmount", {}).get("amount", "0"),
                        "decimals": info.get("tokenAmount", {}).get("decimals", 0),
                    })
            except Exception as e:
                logger.warning(f"Error parsing token account: {e}")
                continue
        
        return parsed_accounts
    
    async def get_top_holders(self, mint_address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get top token holders.
        
        Args:
            mint_address: The token mint address
            limit: Maximum number of holders to return
            
        Returns:
            List of holder information sorted by balance
        """
        accounts = await self.get_token_accounts_by_mint(mint_address, limit * 2)  # Get more to filter
        
        if not accounts:
            return []
        
        # Filter out zero balance accounts and sort by balance
        holders = []
        for account in accounts:
            try:
                balance = Decimal(account.get("balance", "0"))
                if balance > 0:
                    holders.append({
                        "address": account["address"],
                        "balance": balance,
                        "owner": account["owner"],
                    })
            except (ValueError, TypeError):
                continue
        
        # Sort by balance descending
        holders.sort(key=lambda x: x["balance"], reverse=True)
        
        return holders[:limit]
    
    async def get_authority_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get mint and freeze authority information.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with authority information or None if failed
        """
        # This is a simplified implementation
        # In practice, you'd need to decode the mint account data to get authority info
        # For now, we'll return placeholder data
        
        return {
            "mint_authority": None,  # Would need to decode mint account data
            "freeze_authority": None,  # Would need to decode mint account data
            "is_mint_authority_renounced": False,  # Would need to check if authority is None
            "is_freeze_authority_renounced": False,  # Would need to check if authority is None
        }
    
    async def get_token_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive token information from Solana chain.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with comprehensive token information
        """
        # Fetch multiple data sources concurrently
        mint_info_task = self.get_mint_info(mint_address)
        supply_task = self.get_token_supply(mint_address)
        holders_task = self.get_top_holders(mint_address, 50)
        authority_task = self.get_authority_info(mint_address)
        
        mint_info, supply, holders, authority = await asyncio.gather(
            mint_info_task, supply_task, holders_task, authority_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(mint_info, Exception):
            logger.warning(f"Error fetching mint info: {mint_info}")
            mint_info = None
        if isinstance(supply, Exception):
            logger.warning(f"Error fetching supply: {supply}")
            supply = None
        if isinstance(holders, Exception):
            logger.warning(f"Error fetching holders: {holders}")
            holders = []
        if isinstance(authority, Exception):
            logger.warning(f"Error fetching authority: {authority}")
            authority = None
        
        # Calculate total supply
        total_supply = None
        if supply and "value" in supply:
            try:
                total_supply = Decimal(supply["value"]["amount"])
            except (ValueError, TypeError, KeyError):
                pass
        
        # Calculate holder percentages
        if holders and total_supply:
            for holder in holders:
                try:
                    balance = holder["balance"]
                    percentage = (balance / total_supply) * 100
                    holder["percentage"] = float(percentage)
                except (ValueError, TypeError, ZeroDivisionError):
                    holder["percentage"] = 0.0
        
        return {
            "address": mint_address,
            "mint_info": mint_info,
            "supply": supply,
            "total_supply": total_supply,
            "holders": holders,
            "authority": authority,
        }


# Import asyncio for gather
import asyncio
