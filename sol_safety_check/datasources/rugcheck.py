"""RugCheck API client for fetching token risk information."""

import logging
from typing import Any, Dict, Optional

from ..utils import get_env_var, make_http_request

logger = logging.getLogger(__name__)


class RugCheckClient:
    """Client for interacting with RugCheck API."""
    
    BASE_URL = "https://api.rugcheck.xyz/v1"
    
    def __init__(self):
        """Initialize RugCheck client with JWT token if available."""
        self.jwt_token = get_env_var("RUGCHECK_JWT")
        self.headers = {}
        if self.jwt_token:
            self.headers["Authorization"] = f"Bearer {self.jwt_token}"
            logger.info("RugCheck JWT token found, using authenticated requests")
        else:
            logger.warning("No RugCheck JWT token found, skipping RugCheck analysis")
    
    async def get_risk_summary(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get risk summary for a token from RugCheck.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with risk summary or None if failed
        """
        if not self.jwt_token:
            logger.warning("RugCheck risk summary requires JWT token")
            return None
        
        url = f"{self.BASE_URL}/tokens/{mint_address}/risk-summary"
        
        success, data, error = await make_http_request(
            url, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch risk summary from RugCheck: {error}")
            return None
        
        return data
    
    async def get_token_analysis(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive token analysis from RugCheck.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with token analysis or None if failed
        """
        if not self.jwt_token:
            logger.warning("RugCheck token analysis requires JWT token")
            return None
        
        url = f"{self.BASE_URL}/tokens/{mint_address}/analysis"
        
        success, data, error = await make_http_request(
            url, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch token analysis from RugCheck: {error}")
            return None
        
        return data
    
    async def get_holder_analysis(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get holder analysis for a token from RugCheck.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with holder analysis or None if failed
        """
        if not self.jwt_token:
            logger.warning("RugCheck holder analysis requires JWT token")
            return None
        
        url = f"{self.BASE_URL}/tokens/{mint_address}/holders"
        
        success, data, error = await make_http_request(
            url, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch holder analysis from RugCheck: {error}")
            return None
        
        return data
    
    async def get_liquidity_analysis(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get liquidity analysis for a token from RugCheck.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with liquidity analysis or None if failed
        """
        if not self.jwt_token:
            logger.warning("RugCheck liquidity analysis requires JWT token")
            return None
        
        url = f"{self.BASE_URL}/tokens/{mint_address}/liquidity"
        
        success, data, error = await make_http_request(
            url, 
            headers=self.headers
        )
        
        if not success or not data:
            logger.warning(f"Failed to fetch liquidity analysis from RugCheck: {error}")
            return None
        
        return data
    
    async def get_token_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive token information from RugCheck.
        
        Args:
            mint_address: The token mint address
            
        Returns:
            Dictionary with comprehensive token information
        """
        if not self.jwt_token:
            logger.warning("RugCheck token info requires JWT token")
            return None
        
        # Try to get risk summary first (most important)
        risk_summary = await self.get_risk_summary(mint_address)
        
        if not risk_summary:
            return None
        
        # Try to get additional analysis if available
        try:
            analysis = await self.get_token_analysis(mint_address)
            holder_analysis = await self.get_holder_analysis(mint_address)
            liquidity_analysis = await self.get_liquidity_analysis(mint_address)
        except Exception as e:
            logger.warning(f"Error fetching additional RugCheck data: {e}")
            analysis = None
            holder_analysis = None
            liquidity_analysis = None
        
        return {
            "address": mint_address,
            "risk_summary": risk_summary,
            "analysis": analysis,
            "holder_analysis": holder_analysis,
            "liquidity_analysis": liquidity_analysis,
        }
    
    def parse_risk_level(self, risk_data: Dict[str, Any]) -> Optional[str]:
        """
        Parse risk level from RugCheck data.
        
        Args:
            risk_data: Risk data from RugCheck
            
        Returns:
            Risk level string (high, medium, low) or None
        """
        if not risk_data:
            return None
        
        # Try to extract risk level from various possible fields
        risk_level = risk_data.get("risk_level") or risk_data.get("riskLevel") or risk_data.get("level")
        
        if risk_level:
            return str(risk_level).lower()
        
        # Try to parse from score
        risk_score = risk_data.get("risk_score") or risk_data.get("riskScore") or risk_data.get("score")
        
        if risk_score is not None:
            try:
                score = float(risk_score)
                if score >= 80:
                    return "high"
                elif score >= 50:
                    return "medium"
                else:
                    return "low"
            except (ValueError, TypeError):
                pass
        
        return None
