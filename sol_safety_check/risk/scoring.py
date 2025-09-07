"""Risk scoring system for aggregating and calculating final risk scores."""

import logging
from typing import Any, Dict, List, Optional

from ..models import RiskNote, RiskReport
from .rules import RiskRules

logger = logging.getLogger(__name__)


class RiskScorer:
    """Risk scoring system that aggregates individual rule scores."""
    
    def __init__(self):
        """Initialize risk scorer with default configuration."""
        self.rules = RiskRules()
    
    def calculate_overall_score(self, notes: List[RiskNote]) -> int:
        """
        Calculate overall risk score from individual rule notes.
        
        Args:
            notes: List of RiskNote objects
            
        Returns:
            Overall risk score (0-100)
        """
        if not notes:
            return 50  # Default to medium risk if no data
        
        # Calculate weighted average
        total_weight = 0
        weighted_sum = 0
        
        for note in notes:
            weight = self.rules.weights.get(note.rule_name.lower().replace(".", ""), 0.1)
            weighted_sum += note.score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 50
        
        overall_score = weighted_sum / total_weight
        
        # Ensure score is within bounds
        return max(0, min(100, int(overall_score)))
    
    def get_risk_level(self, score: int) -> str:
        """
        Convert risk score to risk level.
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            Risk level string
        """
        if score <= 29:
            return "safe"
        elif score <= 59:
            return "caution"
        else:
            return "high_risk"
    
    def get_verdict(self, score: int) -> str:
        """
        Convert risk score to verdict string.
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            Verdict string
        """
        if score <= 29:
            return "Likely OK (still DYOR)"
        elif score <= 59:
            return "Caution"
        else:
            return "High Risk / Avoid"
    
    def get_verdict_emoji(self, score: int) -> str:
        """
        Get emoji for verdict.
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            Emoji string
        """
        if score <= 29:
            return "✅"
        elif score <= 59:
            return "⚠️"
        else:
            return "❌"
    
    def assess_token_risk(
        self,
        mint_address: str,
        token_meta: Optional[Dict[str, Any]] = None,
        pairs: List[Dict[str, Any]] = None,
        holders: List[Dict[str, Any]] = None,
        liquidity_lock: Optional[Dict[str, Any]] = None,
        trading_info: Optional[Dict[str, Any]] = None,
        pump_fun_info: Optional[Dict[str, Any]] = None,
        rugcheck_data: Optional[Dict[str, Any]] = None,
        data_sources_used: List[str] = None,
        warnings: List[str] = None,
    ) -> RiskReport:
        """
        Assess comprehensive token risk.
        
        Args:
            mint_address: Token mint address
            token_meta: Token metadata
            pairs: Trading pairs
            holders: Holder information
            liquidity_lock: Liquidity lock information
            trading_info: Trading information
            pump_fun_info: Pump.fun information
            rugcheck_data: RugCheck data
            data_sources_used: List of data sources used
            warnings: List of warnings
            
        Returns:
            Complete RiskReport
        """
        if pairs is None:
            pairs = []
        if holders is None:
            holders = []
        if data_sources_used is None:
            data_sources_used = []
        if warnings is None:
            warnings = []
        
        # Run all risk rules
        notes = []
        
        # Authorities check
        notes.append(self.rules.check_authorities(token_meta))
        
        # Liquidity check
        notes.append(self.rules.check_liquidity(pairs, liquidity_lock))
        
        # Tradeability check
        notes.append(self.rules.check_tradeability(trading_info))
        
        # Concentration check
        notes.append(self.rules.check_concentration(holders))
        
        # Age/Hype check
        notes.append(self.rules.check_age_hype(pairs))
        
        # Pump.fun check
        notes.append(self.rules.check_pump_fun(pump_fun_info))
        
        # Listings check
        notes.append(self.rules.check_listings(pairs))
        
        # RugCheck override
        if rugcheck_data:
            notes.append(self.rules.check_rugcheck_override(rugcheck_data))
        
        # Calculate overall score
        overall_score = self.calculate_overall_score(notes)
        risk_level = self.get_risk_level(overall_score)
        verdict = self.get_verdict(overall_score)
        
        # Create risk report
        return RiskReport(
            mint_address=mint_address,
            overall_score=overall_score,
            verdict=verdict,
            risk_level=risk_level,
            notes=notes,
            token_meta=token_meta,
            pairs=pairs,
            top_holders=holders,
            liquidity_lock=liquidity_lock,
            trading_info=trading_info,
            pump_fun_info=pump_fun_info,
            data_sources_used=data_sources_used,
            warnings=warnings,
        )
    
    def get_risk_summary(self, report: RiskReport) -> Dict[str, Any]:
        """
        Get a summary of the risk assessment.
        
        Args:
            report: RiskReport object
            
        Returns:
            Dictionary with risk summary
        """
        # Count notes by severity
        severity_counts = {"low": 0, "medium": 0, "high": 0}
        for note in report.notes:
            severity_counts[note.severity] += 1
        
        # Get top concerns
        high_risk_notes = [note for note in report.notes if note.severity == "high"]
        medium_risk_notes = [note for note in report.notes if note.severity == "medium"]
        
        return {
            "overall_score": report.overall_score,
            "risk_level": report.risk_level,
            "verdict": report.verdict,
            "verdict_emoji": self.get_verdict_emoji(report.overall_score),
            "severity_counts": severity_counts,
            "high_risk_notes": [note.message for note in high_risk_notes],
            "medium_risk_notes": [note.message for note in medium_risk_notes],
            "total_notes": len(report.notes),
            "data_sources_used": report.data_sources_used,
            "warnings": report.warnings,
        }
    
    def format_risk_notes(self, notes: List[RiskNote]) -> List[str]:
        """
        Format risk notes for display.
        
        Args:
            notes: List of RiskNote objects
            
        Returns:
            List of formatted note strings
        """
        formatted_notes = []
        
        for note in notes:
            severity_emoji = {
                "low": "🟢",
                "medium": "🟡", 
                "high": "🔴"
            }.get(note.severity, "⚪")
            
            formatted_notes.append(
                f"{severity_emoji} {note.rule_name}: {note.message} (Score: {note.score})"
            )
        
        return formatted_notes
