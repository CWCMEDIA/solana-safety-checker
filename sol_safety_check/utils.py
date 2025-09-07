"""Utility functions for the Sol Safety Check application."""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with optional default."""
    return os.getenv(key, default)


def validate_solana_address(address: str) -> bool:
    """Validate if a string is a valid Solana address."""
    if not address or not isinstance(address, str):
        return False
    
    # Basic Solana address validation (43-44 characters, base58)
    if len(address) not in [43, 44]:
        return False
    
    # Check if it contains only valid base58 characters (excluding O, I, l)
    valid_chars = set("0123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
    if not all(c in valid_chars for c in address):
        return False
    
    return True


async def make_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: float = 30.0,
    retries: int = 3,
    backoff_factor: float = 1.0,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Make an HTTP request with retry logic and error handling.
    
    Returns:
        Tuple of (success, data, error_message)
    """
    if headers is None:
        headers = {}
    
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json_data,
                )
                
                if response.status_code == 200:
                    return True, response.json(), None
                elif response.status_code == 429:  # Rate limited
                    if attempt < retries:
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        return False, None, f"Rate limited after {retries} retries"
                else:
                    return False, None, f"HTTP {response.status_code}: {response.text}"
                    
        except httpx.TimeoutException:
            if attempt < retries:
                wait_time = backoff_factor * (2 ** attempt)
                logger.warning(f"Request timeout, waiting {wait_time}s before retry {attempt + 1}")
                await asyncio.sleep(wait_time)
                continue
            else:
                return False, None, f"Request timeout after {retries} retries"
        except Exception as e:
            if attempt < retries:
                wait_time = backoff_factor * (2 ** attempt)
                logger.warning(f"Request failed: {e}, waiting {wait_time}s before retry {attempt + 1}")
                await asyncio.sleep(wait_time)
                continue
            else:
                return False, None, f"Request failed: {str(e)}"
    
    return False, None, "Max retries exceeded"


def calculate_percentage(part: float, total: float) -> float:
    """Calculate percentage with safe division."""
    if total == 0:
        return 0.0
    return (part / total) * 100


def format_number(num: float, decimals: int = 2) -> str:
    """Format a number with appropriate decimal places."""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.{decimals}f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.{decimals}f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.{decimals}f}K"
    else:
        return f"{num:.{decimals}f}"


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount with appropriate symbols."""
    if currency.upper() == "USD":
        return f"${format_number(amount)}"
    elif currency.upper() == "SOL":
        return f"{format_number(amount)} SOL"
    else:
        return f"{format_number(amount)} {currency}"


def get_risk_level(score: int) -> str:
    """Convert risk score to risk level string."""
    if score <= 29:
        return "safe"
    elif score <= 59:
        return "caution"
    else:
        return "high_risk"


def get_verdict(score: int) -> str:
    """Convert risk score to verdict string."""
    if score <= 29:
        return "Likely OK (still DYOR)"
    elif score <= 59:
        return "Caution"
    else:
        return "High Risk / Avoid"


def get_verdict_emoji(score: int) -> str:
    """Get emoji for verdict."""
    if score <= 29:
        return "✅"
    elif score <= 59:
        return "⚠️"
    else:
        return "❌"


def is_pump_fun_token(mint_address: str) -> bool:
    """Check if token appears to be from Pump.fun based on address pattern."""
    # Pump.fun tokens often have specific patterns or can be detected via metadata
    # This is a heuristic - in practice, you'd check metadata or use API calls
    return mint_address.endswith("pump") or len(mint_address) == 44


def calculate_holder_concentration(holders: List[Dict[str, Any]]) -> Tuple[float, float]:
    """Calculate top 1% and top 10% holder concentration."""
    if not holders:
        return 0.0, 0.0
    
    # Sort by balance descending
    sorted_holders = sorted(holders, key=lambda x: float(x.get("balance", 0)), reverse=True)
    
    total_holders = len(sorted_holders)
    top_1_percent_count = max(1, total_holders // 100)
    top_10_percent_count = max(1, total_holders // 10)
    
    top_1_percent_balance = sum(float(h.get("balance", 0)) for h in sorted_holders[:top_1_percent_count])
    top_10_percent_balance = sum(float(h.get("balance", 0)) for h in sorted_holders[:top_10_percent_count])
    
    total_balance = sum(float(h.get("balance", 0)) for h in sorted_holders)
    
    if total_balance == 0:
        return 0.0, 0.0
    
    top_1_percent = (top_1_percent_balance / total_balance) * 100
    top_10_percent = (top_10_percent_balance / total_balance) * 100
    
    return top_1_percent, top_10_percent
