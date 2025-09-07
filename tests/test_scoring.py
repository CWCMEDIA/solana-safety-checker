"""Tests for risk scoring system."""

import pytest
from datetime import datetime

from sol_safety_check.risk.scoring import RiskScorer
from sol_safety_check.models import RiskNote


class TestRiskScorer:
    """Test cases for risk scoring system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = RiskScorer()
    
    def test_calculate_overall_score_empty(self):
        """Test overall score calculation with empty notes."""
        notes = []
        score = self.scorer.calculate_overall_score(notes)
        assert score == 50  # Default to medium risk
    
    def test_calculate_overall_score_single_note(self):
        """Test overall score calculation with single note."""
        notes = [
            RiskNote(
                rule_name="Authorities",
                score=20,
                message="Test message",
                severity="medium"
            )
        ]
        score = self.scorer.calculate_overall_score(notes)
        assert score == 20
    
    def test_calculate_overall_score_multiple_notes(self):
        """Test overall score calculation with multiple notes."""
        notes = [
            RiskNote(
                rule_name="Authorities",
                score=20,
                message="Test message 1",
                severity="medium"
            ),
            RiskNote(
                rule_name="Liquidity",
                score=40,
                message="Test message 2",
                severity="high"
            ),
        ]
        score = self.scorer.calculate_overall_score(notes)
        # Should be weighted average based on rule weights
        assert 20 <= score <= 40
    
    def test_get_risk_level_safe(self):
        """Test risk level for safe score."""
        assert self.scorer.get_risk_level(15) == "safe"
        assert self.scorer.get_risk_level(29) == "safe"
    
    def test_get_risk_level_caution(self):
        """Test risk level for caution score."""
        assert self.scorer.get_risk_level(30) == "caution"
        assert self.scorer.get_risk_level(45) == "caution"
        assert self.scorer.get_risk_level(59) == "caution"
    
    def test_get_risk_level_high_risk(self):
        """Test risk level for high risk score."""
        assert self.scorer.get_risk_level(60) == "high_risk"
        assert self.scorer.get_risk_level(85) == "high_risk"
        assert self.scorer.get_risk_level(100) == "high_risk"
    
    def test_get_verdict_safe(self):
        """Test verdict for safe score."""
        assert self.scorer.get_verdict(15) == "Likely OK (still DYOR)"
        assert self.scorer.get_verdict(29) == "Likely OK (still DYOR)"
    
    def test_get_verdict_caution(self):
        """Test verdict for caution score."""
        assert self.scorer.get_verdict(30) == "Caution"
        assert self.scorer.get_verdict(45) == "Caution"
        assert self.scorer.get_verdict(59) == "Caution"
    
    def test_get_verdict_high_risk(self):
        """Test verdict for high risk score."""
        assert self.scorer.get_verdict(60) == "High Risk / Avoid"
        assert self.scorer.get_verdict(85) == "High Risk / Avoid"
        assert self.scorer.get_verdict(100) == "High Risk / Avoid"
    
    def test_get_verdict_emoji_safe(self):
        """Test verdict emoji for safe score."""
        assert self.scorer.get_verdict_emoji(15) == "✅"
        assert self.scorer.get_verdict_emoji(29) == "✅"
    
    def test_get_verdict_emoji_caution(self):
        """Test verdict emoji for caution score."""
        assert self.scorer.get_verdict_emoji(30) == "⚠️"
        assert self.scorer.get_verdict_emoji(45) == "⚠️"
        assert self.scorer.get_verdict_emoji(59) == "⚠️"
    
    def test_get_verdict_emoji_high_risk(self):
        """Test verdict emoji for high risk score."""
        assert self.scorer.get_verdict_emoji(60) == "❌"
        assert self.scorer.get_verdict_emoji(85) == "❌"
        assert self.scorer.get_verdict_emoji(100) == "❌"
    
    def test_assess_token_risk_minimal_data(self):
        """Test token risk assessment with minimal data."""
        report = self.scorer.assess_token_risk(
            mint_address="test_mint_address",
            token_meta=None,
            pairs=[],
            holders=[],
            liquidity_lock=None,
            trading_info=None,
            pump_fun_info=None,
            rugcheck_data=None,
            data_sources_used=[],
            warnings=[],
        )
        
        assert report.mint_address == "test_mint_address"
        assert 0 <= report.overall_score <= 100
        assert report.risk_level in ["safe", "caution", "high_risk"]
        assert report.verdict in ["Likely OK (still DYOR)", "Caution", "High Risk / Avoid"]
        assert len(report.notes) > 0
        assert report.data_sources_used == []
        assert report.warnings == []
    
    def test_assess_token_risk_with_data(self):
        """Test token risk assessment with sample data."""
        token_meta = {
            "address": "test_mint_address",
            "supply": 1000000,
            "mint_authority": None,
            "freeze_authority": None,
            "is_mint_authority_renounced": True,
            "is_freeze_authority_renounced": True,
        }
        
        pairs = [
            {
                "pair_address": "test_pair",
                "base_token": {"address": "test_token", "symbol": "TEST"},
                "quote_token": {"address": "SOL", "symbol": "SOL"},
                "liquidity_usd": 50000,
                "dex_id": "raydium",
                "volume_24h_usd": 10000,
            }
        ]
        
        holders = [
            {"address": "holder1", "balance": 1000, "percentage": 5.0},
            {"address": "holder2", "balance": 800, "percentage": 4.0},
        ]
        
        report = self.scorer.assess_token_risk(
            mint_address="test_mint_address",
            token_meta=token_meta,
            pairs=pairs,
            holders=holders,
            liquidity_lock={"is_locked": True, "locked_percentage": 80},
            trading_info={"can_buy": True, "can_sell": True},
            pump_fun_info={"is_pump_fun_token": False},
            rugcheck_data=None,
            data_sources_used=["dexscreener", "birdeye"],
            warnings=[],
        )
        
        assert report.mint_address == "test_mint_address"
        assert 0 <= report.overall_score <= 100
        assert report.risk_level in ["safe", "caution", "high_risk"]
        assert len(report.notes) > 0
        assert "dexscreener" in report.data_sources_used
        assert "birdeye" in report.data_sources_used
    
    def test_get_risk_summary(self):
        """Test risk summary generation."""
        report = self.scorer.assess_token_risk(
            mint_address="test_mint_address",
            token_meta=None,
            pairs=[],
            holders=[],
            liquidity_lock=None,
            trading_info=None,
            pump_fun_info=None,
            rugcheck_data=None,
            data_sources_used=["dexscreener"],
            warnings=["Test warning"],
        )
        
        summary = self.scorer.get_risk_summary(report)
        
        assert "overall_score" in summary
        assert "risk_level" in summary
        assert "verdict" in summary
        assert "verdict_emoji" in summary
        assert "severity_counts" in summary
        assert "high_risk_notes" in summary
        assert "medium_risk_notes" in summary
        assert "total_notes" in summary
        assert "data_sources_used" in summary
        assert "warnings" in summary
        
        assert summary["overall_score"] == report.overall_score
        assert summary["risk_level"] == report.risk_level
        assert summary["verdict"] == report.verdict
        assert summary["data_sources_used"] == report.data_sources_used
        assert summary["warnings"] == report.warnings
    
    def test_format_risk_notes(self):
        """Test risk notes formatting."""
        notes = [
            RiskNote(
                rule_name="Authorities",
                score=20,
                message="Test message 1",
                severity="medium"
            ),
            RiskNote(
                rule_name="Liquidity",
                score=40,
                message="Test message 2",
                severity="high"
            ),
        ]
        
        formatted = self.scorer.format_risk_notes(notes)
        
        assert len(formatted) == 2
        assert "Authorities" in formatted[0]
        assert "Test message 1" in formatted[0]
        assert "Score: 20" in formatted[0]
        assert "🟡" in formatted[0]  # Medium severity emoji
        
        assert "Liquidity" in formatted[1]
        assert "Test message 2" in formatted[1]
        assert "Score: 40" in formatted[1]
        assert "🔴" in formatted[1]  # High severity emoji
