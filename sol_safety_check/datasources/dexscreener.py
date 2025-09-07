"""DEX Screener API client for fetching token pair information."""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..models import Pair
from ..utils import make_http_request

logger = logging.getLogger(__name__)


class DexScreenerClient:
    """Client for interacting with DEX Screener API."""
    
    BASE_URL = "https://api.dexscreener.com/latest"
    
    async def get_pairs_by_token(self, mint_address: str) -> List[Pair]:
        """
        Get trading pairs for a token from DEX Screener.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            List of Pair objects
        """
        url = f"{self.BASE_URL}/dex/tokens/{mint_address}"
        
        success, data, error = await make_http_request(url)
        
        if not success or not data:
            logger.warning(f"Failed to fetch pairs from DEX Screener: {error}")
            return []
        
        pairs = []
        pairs_data = data.get("pairs", [])
        
        for pair_data in pairs_data:
            try:
                pair = self._parse_pair_data(pair_data)
                if pair:
                    pairs.append(pair)
            except Exception as e:
                logger.warning(f"Failed to parse pair data: {e}")
                continue
        
        return pairs
    
    def _parse_pair_data(self, data: Dict[str, Any]) -> Optional[Pair]:
        """Parse raw pair data from DEX Screener API."""
        try:
            # Extract basic pair information
            pair_address = data.get("pairAddress", "")
            base_token = data.get("baseToken", {})
            quote_token = data.get("quoteToken", {})
            
            # Parse price information
            price_usd = None
            price_native = None
            if "priceUsd" in data and data["priceUsd"]:
                try:
                    price_usd = Decimal(str(data["priceUsd"]))
                except (ValueError, TypeError):
                    pass
            
            if "priceNative" in data and data["priceNative"]:
                try:
                    price_native = Decimal(str(data["priceNative"]))
                except (ValueError, TypeError):
                    pass
            
            # Parse liquidity information
            liquidity_usd = None
            liquidity_native = None
            if "liquidity" in data and data["liquidity"]:
                try:
                    liquidity_usd = Decimal(str(data["liquidity"]["usd"]))
                except (ValueError, TypeError, KeyError):
                    pass
                
                try:
                    liquidity_native = Decimal(str(data["liquidity"]["usd"]))  # Assuming USD for now
                except (ValueError, TypeError, KeyError):
                    pass
            
            # Parse FDV
            fdv_usd = None
            if "fdv" in data and data["fdv"]:
                try:
                    fdv_usd = Decimal(str(data["fdv"]))
                except (ValueError, TypeError):
                    pass
            
            # Parse volume information
            volume_24h_usd = None
            volume_24h_native = None
            if "volume" in data and data["volume"]:
                try:
                    volume_24h_usd = Decimal(str(data["volume"]["h24"]))
                except (ValueError, TypeError, KeyError):
                    pass
                
                try:
                    volume_24h_native = Decimal(str(data["volume"]["h24"]))  # Assuming same as USD for now
                except (ValueError, TypeError, KeyError):
                    pass
            
            # Parse transaction count
            txns_24h = None
            if "txns" in data and data["txns"]:
                try:
                    txns_24h = int(data["txns"]["h24"]["buys"]) + int(data["txns"]["h24"]["sells"])
                except (ValueError, TypeError, KeyError):
                    pass
            
            # Parse creation time
            pair_created_at = None
            if "pairCreatedAt" in data and data["pairCreatedAt"]:
                try:
                    pair_created_at = datetime.fromtimestamp(data["pairCreatedAt"] / 1000)
                except (ValueError, TypeError, OSError):
                    pass
            
            # Extract DEX information
            dex_id = data.get("dexId", "")
            router = data.get("url", "")
            
            return Pair(
                pair_address=pair_address,
                base_token=base_token,
                quote_token=quote_token,
                price_usd=price_usd,
                price_native=price_native,
                liquidity_usd=liquidity_usd,
                liquidity_native=liquidity_native,
                fdv_usd=fdv_usd,
                volume_24h_usd=volume_24h_usd,
                volume_24h_native=volume_24h_native,
                txns_24h=txns_24h,
                pair_created_at=pair_created_at,
                dex_id=dex_id,
                router=router,
            )
            
        except Exception as e:
            logger.error(f"Error parsing pair data: {e}")
            return None
    
    async def get_trending_tokens(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get trending tokens from DEX Screener.
        
        Args:
            limit: Maximum number of tokens to return
            
        Returns:
            List of trending token dictionaries
        """
        # Try multiple search terms to get more diverse results
        search_terms = ["solana", "pump", "meme", "new"]
        all_tokens = []
        seen_tokens = set()
        
        for search_term in search_terms:
            url = f"{self.BASE_URL}/dex/search/?q={search_term}"
            
            success, data, error = await make_http_request(url)
            
            if not success or not data:
                continue
            
            pairs_data = data.get("pairs", [])
            
            for pair_data in pairs_data[:limit * 3]:  # Get more pairs to ensure we have enough unique tokens
                try:
                    # Only include Solana chain tokens
                    if pair_data.get("chainId") != "solana":
                        continue
                    
                    base_token = pair_data.get("baseToken", {})
                    token_address = base_token.get("address", "")
                    
                    if not token_address or token_address in seen_tokens:
                        continue
                    
                    seen_tokens.add(token_address)
                    
                    # Extract token information
                    token_info = {
                        "address": token_address,
                        "symbol": base_token.get("symbol", ""),
                        "name": base_token.get("name", ""),
                        "price": float(pair_data.get("priceUsd", 0)),
                        "change24h": float(pair_data.get("priceChange", {}).get("h24", 0)),
                        "volume24h": float(pair_data.get("volume", {}).get("h24", 0)),
                        "liquidity": float(pair_data.get("liquidity", {}).get("usd", 0)),
                        "dex_id": pair_data.get("dexId", ""),
                        "pair_address": pair_data.get("pairAddress", ""),
                    }
                    
                    all_tokens.append(token_info)
                    
                    if len(all_tokens) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"Failed to parse trending token data: {e}")
                    continue
            
            if len(all_tokens) >= limit:
                break
        
        return all_tokens[:limit]
    
    async def get_latest_tokens(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get latest/newly created tokens from DEX Screener.
        
        Args:
            limit: Maximum number of tokens to return
            
        Returns:
            List of latest token dictionaries
        """
        # Use multiple search terms to get more diverse results
        search_terms = ["new", "pump", "meme", "solana"]
        all_tokens = []
        seen_tokens = set()
        
        for search_term in search_terms:
            url = f"{self.BASE_URL}/dex/search/?q={search_term}"
            
            success, data, error = await make_http_request(url)
            
            if not success or not data:
                continue
            
            pairs_data = data.get("pairs", [])
            
            for pair_data in pairs_data[:limit * 3]:  # Get more pairs to ensure we have enough unique tokens
                try:
                    # Only include Solana chain tokens
                    if pair_data.get("chainId") != "solana":
                        continue
                    
                    base_token = pair_data.get("baseToken", {})
                    token_address = base_token.get("address", "")
                    
                    if not token_address or token_address in seen_tokens:
                        continue
                    
                    seen_tokens.add(token_address)
                    
                    # Calculate token age (rough estimate based on pair creation)
                    pair_created_at = pair_data.get("pairCreatedAt", 0)
                    current_time = datetime.now().timestamp() * 1000  # Convert to milliseconds
                    age_hours = (current_time - pair_created_at) / (1000 * 60 * 60) if pair_created_at else 0
                    
                    # Be more inclusive - include tokens up to 90 days old
                    if age_hours > 2160:  # 90 days
                        continue
                    
                    # Extract token information
                    token_info = {
                        "address": token_address,
                        "symbol": base_token.get("symbol", ""),
                        "name": base_token.get("name", ""),
                        "price": float(pair_data.get("priceUsd", 0)),
                        "change24h": float(pair_data.get("priceChange", {}).get("h24", 0)),
                        "volume24h": float(pair_data.get("volume", {}).get("h24", 0)),
                        "liquidity": float(pair_data.get("liquidity", {}).get("usd", 0)),
                        "dex_id": pair_data.get("dexId", ""),
                        "pair_address": pair_data.get("pairAddress", ""),
                        "age": f"{int(age_hours)} hours" if age_hours < 24 else f"{int(age_hours/24)} days",
                    }
                    
                    all_tokens.append(token_info)
                    
                    if len(all_tokens) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f"Failed to parse latest token data: {e}")
                    continue
            
            if len(all_tokens) >= limit:
                break
        
        # Sort by age (newest first) - handle cases where age might be missing
        def sort_key(x):
            age_str = x.get("age", "0 hours")
            try:
                if "hours" in age_str:
                    return int(age_str.split()[0])
                elif "days" in age_str:
                    return int(age_str.split()[0]) * 24
                else:
                    return 0
            except:
                return 0
        
        all_tokens.sort(key=sort_key)
        
        return all_tokens[:limit]

    async def get_token_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get basic token information from DEX Screener.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with token information or None if failed
        """
        pairs = await self.get_pairs_by_token(mint_address)
        
        if not pairs:
            return None
        
        # Use the first pair's base token as the main token info
        main_pair = pairs[0]
        base_token = main_pair.base_token
        
        return {
            "address": base_token.get("address", mint_address),
            "symbol": base_token.get("symbol", ""),
            "name": base_token.get("name", ""),
            "decimals": base_token.get("decimals", 0),
            "pairs": [pair.dict() for pair in pairs],
        }
