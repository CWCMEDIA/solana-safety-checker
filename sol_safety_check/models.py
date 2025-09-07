"""Pydantic models for data structures used throughout the application."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class Pair(BaseModel):
    """Represents a trading pair for a token."""
    
    pair_address: str
    base_token: Dict[str, Any]
    quote_token: Dict[str, Any]
    price_usd: Optional[Decimal] = None
    price_native: Optional[Decimal] = None
    liquidity_usd: Optional[Decimal] = None
    liquidity_native: Optional[Decimal] = None
    fdv_usd: Optional[Decimal] = None
    volume_24h_usd: Optional[Decimal] = None
    volume_24h_native: Optional[Decimal] = None
    txns_24h: Optional[int] = None
    pair_created_at: Optional[datetime] = None
    dex_id: Optional[str] = None
    router: Optional[str] = None


class TokenMeta(BaseModel):
    """Token metadata and basic information."""
    
    address: str
    symbol: Optional[str] = None
    name: Optional[str] = None
    decimals: Optional[int] = None
    supply: Optional[Decimal] = None
    mint_authority: Optional[str] = None
    freeze_authority: Optional[str] = None
    is_mint_authority_renounced: bool = False
    is_freeze_authority_renounced: bool = False


class HolderStat(BaseModel):
    """Holder statistics for a token."""
    
    address: str
    balance: Decimal
    percentage: Decimal
    is_insider: bool = False
    is_dev_wallet: bool = False


class LiquidityLock(BaseModel):
    """Liquidity lock information."""
    
    is_locked: bool = False
    locked_percentage: Optional[Decimal] = None
    lock_duration_days: Optional[int] = None
    lock_provider: Optional[str] = None
    lock_expiry: Optional[datetime] = None


class TradingInfo(BaseModel):
    """Trading-related information."""
    
    can_buy: bool = True
    can_sell: bool = True
    buy_tax_percentage: Optional[Decimal] = None
    sell_tax_percentage: Optional[Decimal] = None
    is_honeypot: bool = False
    slippage_tolerance: Optional[Decimal] = None


class PumpFunInfo(BaseModel):
    """Pump.fun specific information."""
    
    is_pump_fun_token: bool = False
    creation_time: Optional[datetime] = None
    dev_wallet: Optional[str] = None
    migration_status: Optional[str] = None
    dev_holdings_percentage: Optional[Decimal] = None


class RiskNote(BaseModel):
    """Individual risk assessment note."""
    
    rule_name: str
    score: int = Field(ge=0, le=100)
    message: str
    severity: str = Field(pattern="^(low|medium|high)$")


class RiskReport(BaseModel):
    """Complete risk assessment report."""
    
    mint_address: str
    overall_score: int = Field(ge=0, le=100)
    verdict: str
    risk_level: str = Field(pattern="^(safe|caution|high_risk)$")
    notes: List[RiskNote]
    token_meta: Optional[TokenMeta] = None
    pairs: List[Pair] = []
    top_holders: List[HolderStat] = []
    liquidity_lock: Optional[LiquidityLock] = None
    trading_info: Optional[TradingInfo] = None
    pump_fun_info: Optional[PumpFunInfo] = None
    data_sources_used: List[str] = []
    warnings: List[str] = []
    generated_at: datetime = Field(default_factory=datetime.now)


class DataSourceResult(BaseModel):
    """Result from a data source with metadata."""
    
    source_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time_ms: Optional[float] = None
