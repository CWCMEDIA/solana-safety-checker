"""Risk assessment rules for evaluating token safety."""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from ..models import RiskNote

logger = logging.getLogger(__name__)


class RiskRules:
    """Collection of risk assessment rules."""
    
    def __init__(self):
        """Initialize risk rules with default weights."""
        # Rule weights (can be adjusted)
        self.weights = {
            "authorities": 0.20,
            "liquidity": 0.25,
            "tradeability": 0.20,
            "concentration": 0.15,
            "age_hype": 0.10,
            "pump_fun": 0.05,
            "listings": 0.05,
        }
    
    def check_authorities(self, token_meta: Optional[Dict[str, Any]]) -> RiskNote:
        """
        Check mint and freeze authority status.
        
        Args:
            token_meta: Token metadata
            
        Returns:
            RiskNote with authority risk assessment
        """
        if not token_meta:
            return RiskNote(
                rule_name="Authorities",
                score=10,
                message="No authority information available",
                severity="medium"
            )
        
        score = 0
        messages = []
        
        # Check mint authority
        mint_authority = token_meta.get("mint_authority")
        is_mint_renounced = token_meta.get("is_mint_authority_renounced", False)
        
        if mint_authority and not is_mint_renounced:
            score += 25
            messages.append("Mint authority not renounced")
        
        # Check freeze authority
        freeze_authority = token_meta.get("freeze_authority")
        is_freeze_renounced = token_meta.get("is_freeze_authority_renounced", False)
        
        if freeze_authority and not is_freeze_renounced:
            score += 15
            messages.append("Freeze authority present")
        
        if not messages:
            messages.append("Authorities properly renounced")
        
        return RiskNote(
            rule_name="Authorities",
            score=min(score, 100),
            message="; ".join(messages),
            severity="high" if score >= 30 else "medium" if score >= 15 else "low"
        )
    
    def check_liquidity(self, pairs: List[Dict[str, Any]], liquidity_lock: Optional[Dict[str, Any]] = None) -> RiskNote:
        """
        Check liquidity levels and lock status.
        
        Args:
            pairs: List of trading pairs
            liquidity_lock: Liquidity lock information
            
        Returns:
            RiskNote with liquidity risk assessment
        """
        if not pairs:
            return RiskNote(
                rule_name="Liquidity",
                score=25,
                message="No trading pairs found",
                severity="high"
            )
        
        score = 0
        messages = []
        
        # Find the pair with highest liquidity
        max_liquidity_usd = 0
        for pair in pairs:
            liquidity = pair.get("liquidity_usd")
            if liquidity and isinstance(liquidity, (int, float, Decimal)):
                max_liquidity_usd = max(max_liquidity_usd, float(liquidity))
        
        # Check liquidity thresholds
        if max_liquidity_usd < 2000:  # Less than $2,000
            score += 25
            messages.append(f"Low liquidity: ${max_liquidity_usd:,.0f}")
        elif max_liquidity_usd < 10000:  # Less than $10,000
            score += 10
            messages.append(f"Moderate liquidity: ${max_liquidity_usd:,.0f}")
        
        # Check liquidity lock
        if liquidity_lock:
            is_locked = liquidity_lock.get("is_locked", False)
            locked_percentage = liquidity_lock.get("locked_percentage")
            lock_duration = liquidity_lock.get("lock_duration_days")
            
            if not is_locked:
                score += 20
                messages.append("No liquidity lock detected")
            elif locked_percentage and locked_percentage < 60:
                score += 15
                messages.append(f"Low lock percentage: {locked_percentage}%")
            elif lock_duration and lock_duration < 7:
                score += 10
                messages.append(f"Short lock duration: {lock_duration} days")
        else:
            score += 10
            messages.append("No lock information available")
        
        if not messages:
            messages.append("Liquidity appears adequate")
        
        return RiskNote(
            rule_name="Liquidity",
            score=min(score, 100),
            message="; ".join(messages),
            severity="high" if score >= 30 else "medium" if score >= 15 else "low"
        )
    
    def check_tradeability(self, trading_info: Optional[Dict[str, Any]]) -> RiskNote:
        """
        Check trading restrictions and taxes.
        
        Args:
            trading_info: Trading information
            
        Returns:
            RiskNote with tradeability risk assessment
        """
        if not trading_info:
            return RiskNote(
                rule_name="Tradeability",
                score=15,
                message="No trading information available",
                severity="medium"
            )
        
        score = 0
        messages = []
        
        # Check if selling is restricted
        can_sell = trading_info.get("can_sell", True)
        if not can_sell:
            score += 35
            messages.append("Cannot sell tokens (honeypot)")
        
        # Check sell tax
        sell_tax = trading_info.get("sell_tax_percentage")
        if sell_tax and sell_tax > 10:
            score += 35
            messages.append(f"High sell tax: {sell_tax}%")
        elif sell_tax and sell_tax > 5:
            score += 15
            messages.append(f"Moderate sell tax: {sell_tax}%")
        
        # Check buy tax
        buy_tax = trading_info.get("buy_tax_percentage")
        if buy_tax and buy_tax > 10:
            score += 15
            messages.append(f"High buy tax: {buy_tax}%")
        
        # Check if it's a honeypot
        is_honeypot = trading_info.get("is_honeypot", False)
        if is_honeypot:
            score += 35
            messages.append("Detected as honeypot")
        
        if not messages:
            messages.append("Trading appears normal")
        
        return RiskNote(
            rule_name="Tradeability",
            score=min(score, 100),
            message="; ".join(messages),
            severity="high" if score >= 30 else "medium" if score >= 15 else "low"
        )
    
    def check_concentration(self, holders: List[Dict[str, Any]]) -> RiskNote:
        """
        Check holder concentration and distribution.
        
        Args:
            holders: List of holder information
            
        Returns:
            RiskNote with concentration risk assessment
        """
        if not holders:
            return RiskNote(
                rule_name="Concentration",
                score=20,
                message="No holder information available",
                severity="medium"
            )
        
        score = 0
        messages = []
        
        # Calculate top holder percentages
        total_holders = len(holders)
        if total_holders == 0:
            return RiskNote(
                rule_name="Concentration",
                score=20,
                message="No holders found",
                severity="medium"
            )
        
        # Get top 1% and top 10% holder counts
        top_1_percent_count = max(1, total_holders // 100)
        top_10_percent_count = max(1, total_holders // 10)
        
        # Calculate percentages
        top_1_percent_balance = sum(
            float(h.get("balance", 0)) for h in holders[:top_1_percent_count]
        )
        top_10_percent_balance = sum(
            float(h.get("balance", 0)) for h in holders[:top_10_percent_count]
        )
        
        total_balance = sum(float(h.get("balance", 0)) for h in holders)
        
        if total_balance > 0:
            top_1_percent = (top_1_percent_balance / total_balance) * 100
            top_10_percent = (top_10_percent_balance / total_balance) * 100
            
            # Check top 10% concentration
            if top_10_percent > 70:
                score += 30
                messages.append(f"High top-10% concentration: {top_10_percent:.1f}%")
            elif top_10_percent > 50:
                score += 15
                messages.append(f"Moderate top-10% concentration: {top_10_percent:.1f}%")
            
            # Check top 1% concentration
            if top_1_percent > 30:
                score += 25
                messages.append(f"High top-1% concentration: {top_1_percent:.1f}%")
            elif top_1_percent > 20:
                score += 10
                messages.append(f"Moderate top-1% concentration: {top_1_percent:.1f}%")
        
        if not messages:
            messages.append("Holder distribution appears healthy")
        
        return RiskNote(
            rule_name="Concentration",
            score=min(score, 100),
            message="; ".join(messages),
            severity="high" if score >= 30 else "medium" if score >= 15 else "low"
        )
    
    def check_age_hype(self, pairs: List[Dict[str, Any]]) -> RiskNote:
        """
        Check token age and hype patterns.
        
        Args:
            pairs: List of trading pairs
            
        Returns:
            RiskNote with age/hype risk assessment
        """
        if not pairs:
            return RiskNote(
                rule_name="Age/Hype",
                score=10,
                message="No trading pairs to analyze",
                severity="low"
            )
        
        score = 0
        messages = []
        
        # Find the oldest pair
        oldest_pair = None
        for pair in pairs:
            created_at = pair.get("pair_created_at")
            if created_at and (oldest_pair is None or created_at < oldest_pair):
                oldest_pair = created_at
        
        if oldest_pair:
            from datetime import datetime, timedelta
            age_hours = (datetime.now() - oldest_pair).total_seconds() / 3600
            
            if age_hours < 24:
                score += 10
                messages.append(f"Very new token: {age_hours:.1f} hours old")
            elif age_hours < 168:  # 1 week
                messages.append(f"New token: {age_hours/24:.1f} days old")
        
        # Check for volume spikes (simplified)
        for pair in pairs:
            volume_24h = pair.get("volume_24h_usd")
            if volume_24h and volume_24h > 1000000:  # $1M+ volume
                if oldest_pair and (datetime.now() - oldest_pair).total_seconds() < 86400:  # < 24 hours
                    score += 10
                    messages.append("High volume on new token (potential PnD)")
                    break
        
        if not messages:
            messages.append("Age and volume patterns appear normal")
        
        return RiskNote(
            rule_name="Age/Hype",
            score=min(score, 100),
            message="; ".join(messages),
            severity="high" if score >= 20 else "medium" if score >= 10 else "low"
        )
    
    def check_pump_fun(self, pump_fun_info: Optional[Dict[str, Any]]) -> RiskNote:
        """
        Check Pump.fun specific risks.
        
        Args:
            pump_fun_info: Pump.fun information
            
        Returns:
            RiskNote with Pump.fun risk assessment
        """
        if not pump_fun_info:
            return RiskNote(
                rule_name="Pump.fun",
                score=0,
                message="Not a Pump.fun token",
                severity="low"
            )
        
        score = 0
        messages = []
        
        is_pump_fun = pump_fun_info.get("is_pump_fun_token", False)
        if not is_pump_fun:
            return RiskNote(
                rule_name="Pump.fun",
                score=0,
                message="Not a Pump.fun token",
                severity="low"
            )
        
        # Check dev wallet holdings
        dev_holdings = pump_fun_info.get("dev_holdings_percentage")
        if dev_holdings and dev_holdings > 20:
            score += 20
            messages.append(f"High dev holdings: {dev_holdings}%")
        
        # Check migration status
        migration_status = pump_fun_info.get("migration_status")
        if migration_status == "not_migrated":
            score += 10
            messages.append("Migration not completed")
        
        if not messages:
            messages.append("Pump.fun token appears normal")
        
        return RiskNote(
            rule_name="Pump.fun",
            score=min(score, 100),
            message="; ".join(messages),
            severity="high" if score >= 20 else "medium" if score >= 10 else "low"
        )
    
    def check_listings(self, pairs: List[Dict[str, Any]]) -> RiskNote:
        """
        Check exchange listings and ecosystem presence.
        
        Args:
            pairs: List of trading pairs
            
        Returns:
            RiskNote with listings risk assessment
        """
        if not pairs:
            return RiskNote(
                rule_name="Listings",
                score=20,
                message="No trading pairs found",
                severity="medium"
            )
        
        score = 0
        messages = []
        
        # Check for major DEXs
        major_dexs = {"raydium", "orca", "jupiter", "meteora"}
        found_dexs = set()
        
        for pair in pairs:
            dex_id = pair.get("dex_id", "").lower()
            if dex_id in major_dexs:
                found_dexs.add(dex_id)
        
        if not found_dexs:
            score += 10
            messages.append("Not on major DEXs")
        elif len(found_dexs) < 2:
            score += 5
            messages.append("Limited DEX presence")
        
        if not messages:
            messages.append("Good DEX presence")
        
        return RiskNote(
            rule_name="Listings",
            score=min(score, 100),
            message="; ".join(messages),
            severity="high" if score >= 15 else "medium" if score >= 5 else "low"
        )
    
    def check_rugcheck_override(self, rugcheck_data: Optional[Dict[str, Any]]) -> RiskNote:
        """
        Apply RugCheck risk override if available.
        
        Args:
            rugcheck_data: RugCheck risk data
            
        Returns:
            RiskNote with RugCheck override
        """
        if not rugcheck_data:
            return RiskNote(
                rule_name="RugCheck",
                score=0,
                message="RugCheck data not available",
                severity="low"
            )
        
        risk_level = rugcheck_data.get("risk_level", "").lower()
        
        if risk_level == "high":
            return RiskNote(
                rule_name="RugCheck",
                score=20,
                message="RugCheck reports HIGH RISK",
                severity="high"
            )
        elif risk_level == "medium":
            return RiskNote(
                rule_name="RugCheck",
                score=10,
                message="RugCheck reports MEDIUM RISK",
                severity="medium"
            )
        else:
            return RiskNote(
                rule_name="RugCheck",
                score=0,
                message="RugCheck reports LOW RISK",
                severity="low"
            )
