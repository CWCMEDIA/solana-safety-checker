"""Tests for risk assessment rules."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta

from sol_safety_check.risk.rules import RiskRules


class TestRiskRules:
    """Test cases for risk rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rules = RiskRules()
    
    def test_check_authorities_renounced(self):
        """Test authority check with renounced authorities."""
        token_meta = {
            "mint_authority": None,
            "freeze_authority": None,
            "is_mint_authority_renounced": True,
            "is_freeze_authority_renounced": True,
        }
        
        note = self.rules.check_authorities(token_meta)
        
        assert note.rule_name == "Authorities"
        assert note.score == 0
        assert note.severity == "low"
        assert "properly renounced" in note.message
    
    def test_check_authorities_not_renounced(self):
        """Test authority check with active authorities."""
        token_meta = {
            "mint_authority": "some_authority_address",
            "freeze_authority": "some_freeze_address",
            "is_mint_authority_renounced": False,
            "is_freeze_authority_renounced": False,
        }
        
        note = self.rules.check_authorities(token_meta)
        
        assert note.rule_name == "Authorities"
        assert note.score == 40  # 25 + 15
        assert note.severity == "high"
        assert "Mint authority not renounced" in note.message
        assert "Freeze authority present" in note.message
    
    def test_check_liquidity_high(self):
        """Test liquidity check with high liquidity."""
        pairs = [
            {
                "liquidity_usd": 50000,
                "dex_id": "raydium",
            }
        ]
        liquidity_lock = {
            "is_locked": True,
            "locked_percentage": 80,
            "lock_duration_days": 30,
        }
        
        note = self.rules.check_liquidity(pairs, liquidity_lock)
        
        assert note.rule_name == "Liquidity"
        assert note.score == 0
        assert note.severity == "low"
        assert "appears adequate" in note.message
    
    def test_check_liquidity_low(self):
        """Test liquidity check with low liquidity."""
        pairs = [
            {
                "liquidity_usd": 1000,
                "dex_id": "raydium",
            }
        ]
        liquidity_lock = {
            "is_locked": False,
            "locked_percentage": 0,
            "lock_duration_days": 0,
        }
        
        note = self.rules.check_liquidity(pairs, liquidity_lock)
        
        assert note.rule_name == "Liquidity"
        assert note.score == 45  # 25 + 20
        assert note.severity == "high"
        assert "Low liquidity" in note.message
        assert "No liquidity lock" in note.message
    
    def test_check_tradeability_normal(self):
        """Test tradeability check with normal trading."""
        trading_info = {
            "can_buy": True,
            "can_sell": True,
            "buy_tax_percentage": 0,
            "sell_tax_percentage": 0,
            "is_honeypot": False,
        }
        
        note = self.rules.check_tradeability(trading_info)
        
        assert note.rule_name == "Tradeability"
        assert note.score == 0
        assert note.severity == "low"
        assert "appears normal" in note.message
    
    def test_check_tradeability_honeypot(self):
        """Test tradeability check with honeypot."""
        trading_info = {
            "can_buy": True,
            "can_sell": False,
            "buy_tax_percentage": 0,
            "sell_tax_percentage": 0,
            "is_honeypot": True,
        }
        
        note = self.rules.check_tradeability(trading_info)
        
        assert note.rule_name == "Tradeability"
        assert note.score == 70  # 35 + 35
        assert note.severity == "high"
        assert "Cannot sell tokens" in note.message
        assert "Detected as honeypot" in note.message
    
    def test_check_concentration_healthy(self):
        """Test concentration check with healthy distribution."""
        holders = [
            {"balance": 1000, "percentage": 5.0},
            {"balance": 800, "percentage": 4.0},
            {"balance": 600, "percentage": 3.0},
            {"balance": 400, "percentage": 2.0},
            {"balance": 200, "percentage": 1.0},
        ] * 20  # 100 holders total
        
        note = self.rules.check_concentration(holders)
        
        assert note.rule_name == "Concentration"
        assert note.score == 0
        assert note.severity == "low"
        assert "appears healthy" in note.message
    
    def test_check_concentration_high(self):
        """Test concentration check with high concentration."""
        holders = [
            {"balance": 5000, "percentage": 50.0},  # Top holder has 50%
            {"balance": 2000, "percentage": 20.0},
            {"balance": 1000, "percentage": 10.0},
            {"balance": 500, "percentage": 5.0},
            {"balance": 100, "percentage": 1.0},
        ] * 2  # 10 holders total
        
        note = self.rules.check_concentration(holders)
        
        assert note.rule_name == "Concentration"
        assert note.score >= 10  # Should have concentration penalty
        assert note.severity in ["low", "medium", "high"]
        assert "concentration" in note.message.lower()
    
    def test_check_age_hype_new_token(self):
        """Test age/hype check with new token."""
        now = datetime.now()
        pairs = [
            {
                "pair_created_at": now - timedelta(hours=2),
                "volume_24h_usd": 2000000,  # High volume
                "dex_id": "raydium",
            }
        ]
        
        note = self.rules.check_age_hype(pairs)
        
        assert note.rule_name == "Age/Hype"
        assert note.score >= 10  # Should have new token penalty
        assert note.severity in ["medium", "high"]
        assert "new token" in note.message.lower()
    
    def test_check_pump_fun_normal(self):
        """Test Pump.fun check with normal token."""
        pump_fun_info = {
            "is_pump_fun_token": True,
            "dev_holdings_percentage": 5,
            "migration_status": "completed",
        }
        
        note = self.rules.check_pump_fun(pump_fun_info)
        
        assert note.rule_name == "Pump.fun"
        assert note.score == 0
        assert note.severity == "low"
        assert "appears normal" in note.message
    
    def test_check_pump_fun_high_dev_holdings(self):
        """Test Pump.fun check with high dev holdings."""
        pump_fun_info = {
            "is_pump_fun_token": True,
            "dev_holdings_percentage": 30,
            "migration_status": "completed",
        }
        
        note = self.rules.check_pump_fun(pump_fun_info)
        
        assert note.rule_name == "Pump.fun"
        assert note.score == 20
        assert note.severity == "high"
        assert "High dev holdings" in note.message
    
    def test_check_listings_good(self):
        """Test listings check with good DEX presence."""
        pairs = [
            {"dex_id": "raydium"},
            {"dex_id": "orca"},
            {"dex_id": "jupiter"},
        ]
        
        note = self.rules.check_listings(pairs)
        
        assert note.rule_name == "Listings"
        assert note.score == 0
        assert note.severity == "low"
        assert "Good DEX presence" in note.message
    
    def test_check_listings_poor(self):
        """Test listings check with poor DEX presence."""
        pairs = [
            {"dex_id": "unknown_dex"},
        ]
        
        note = self.rules.check_listings(pairs)
        
        assert note.rule_name == "Listings"
        assert note.score == 10
        assert note.severity == "medium"
        assert "Not on major DEXs" in note.message
    
    def test_check_rugcheck_override_high(self):
        """Test RugCheck override with high risk."""
        rugcheck_data = {"risk_level": "high"}
        
        note = self.rules.check_rugcheck_override(rugcheck_data)
        
        assert note.rule_name == "RugCheck"
        assert note.score == 20
        assert note.severity == "high"
        assert "HIGH RISK" in note.message
    
    def test_check_rugcheck_override_medium(self):
        """Test RugCheck override with medium risk."""
        rugcheck_data = {"risk_level": "medium"}
        
        note = self.rules.check_rugcheck_override(rugcheck_data)
        
        assert note.rule_name == "RugCheck"
        assert note.score == 10
        assert note.severity == "medium"
        assert "MEDIUM RISK" in note.message
    
    def test_check_rugcheck_override_low(self):
        """Test RugCheck override with low risk."""
        rugcheck_data = {"risk_level": "low"}
        
        note = self.rules.check_rugcheck_override(rugcheck_data)
        
        assert note.rule_name == "RugCheck"
        assert note.score == 0
        assert note.severity == "low"
        assert "LOW RISK" in note.message
