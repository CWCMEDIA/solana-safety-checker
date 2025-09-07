"""CLI interface for Sol Safety Check."""

import asyncio
import json
import logging
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from .datasources.dexscreener import DexScreenerClient
from .datasources.birdeye import BirdeyeClient
from .datasources.rugcheck import RugCheckClient
from .datasources.pumpfun import PumpFunClient
from .datasources.solana_chain import SolanaChainClient
from .risk.scoring import RiskScorer
from .utils import validate_solana_address, get_env_var
from .models import RiskReport

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()

# Initialize CLI app
app = typer.Typer(
    name="sol-safety-check",
    help="A comprehensive Solana token safety checker CLI tool",
    add_completion=False,
)


@app.command()
def main(
    mint: str = typer.Argument(..., help="Solana token mint address"),
    rpc: Optional[str] = typer.Option(None, "--rpc", help="Custom Solana RPC URL"),
    fast: bool = typer.Option(False, "--fast", help="Skip heavier calls for quick analysis"),
    json_output: bool = typer.Option(False, "--json", help="Output results in JSON format"),
    providers: Optional[str] = typer.Option(None, "--providers", help="Comma-separated list of providers to use"),
) -> None:
    """
    Check the safety of a Solana token by analyzing multiple risk factors.
    
    Examples:
        sol-safety-check Fv73EXJBRfctJzLVC3P7uQP6er6JU8b4KtDr4LQFpump
        sol-safety-check <MINT> --json
        sol-safety-check <MINT> --providers dexscreener,birdeye
        sol-safety-check <MINT> --fast
    """
    # Validate mint address
    if not validate_solana_address(mint):
        console.print("[red]Error: Invalid Solana address format[/red]")
        raise typer.Exit(1)
    
    # Parse providers
    enabled_providers = None
    if providers:
        enabled_providers = [p.strip().lower() for p in providers.split(",")]
    
    # Run the analysis
    asyncio.run(run_analysis(mint, rpc, fast, json_output, enabled_providers))


async def run_analysis(
    mint: str,
    rpc: Optional[str],
    fast: bool,
    json_output: bool,
    enabled_providers: Optional[List[str]],
) -> None:
    """Run the token safety analysis."""
    
    # Initialize clients
    clients = {
        "dexscreener": DexScreenerClient(),
        "birdeye": BirdeyeClient(),
        "rugcheck": RugCheckClient(),
        "pumpfun": PumpFunClient(),
        "solana_chain": SolanaChainClient(rpc),
    }
    
    # Filter clients based on enabled providers
    if enabled_providers:
        clients = {k: v for k, v in clients.items() if k in enabled_providers}
    
    # Initialize risk scorer
    risk_scorer = RiskScorer()
    
    # Collect data from all sources
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Create tasks for concurrent data fetching
        tasks = {}
        data_sources_used = []
        warnings = []
        
        # DEX Screener
        if "dexscreener" in clients:
            task = progress.add_task("Fetching data from DEX Screener...", total=None)
            try:
                dexscreener_data = await clients["dexscreener"].get_token_info(mint)
                if dexscreener_data:
                    data_sources_used.append("dexscreener")
                tasks["dexscreener"] = dexscreener_data
            except Exception as e:
                logger.warning(f"DEX Screener error: {e}")
                tasks["dexscreener"] = None
                warnings.append(f"DEX Screener failed: {str(e)}")
            finally:
                progress.update(task, completed=True)
        
        # Birdeye
        if "birdeye" in clients:
            task = progress.add_task("Fetching data from Birdeye...", total=None)
            try:
                birdeye_data = await clients["birdeye"].get_token_info(mint)
                if birdeye_data:
                    data_sources_used.append("birdeye")
                tasks["birdeye"] = birdeye_data
            except Exception as e:
                logger.warning(f"Birdeye error: {e}")
                tasks["birdeye"] = None
                warnings.append(f"Birdeye failed: {str(e)}")
            finally:
                progress.update(task, completed=True)
        
        # RugCheck
        if "rugcheck" in clients:
            task = progress.add_task("Fetching data from RugCheck...", total=None)
            try:
                rugcheck_data = await clients["rugcheck"].get_token_info(mint)
                if rugcheck_data:
                    data_sources_used.append("rugcheck")
                tasks["rugcheck"] = rugcheck_data
            except Exception as e:
                logger.warning(f"RugCheck error: {e}")
                tasks["rugcheck"] = None
                warnings.append(f"RugCheck failed: {str(e)}")
            finally:
                progress.update(task, completed=True)
        
        # Pump.fun
        if "pumpfun" in clients:
            task = progress.add_task("Fetching data from Pump.fun...", total=None)
            try:
                pumpfun_data = await clients["pumpfun"].get_token_info(mint)
                if pumpfun_data:
                    data_sources_used.append("pumpfun")
                tasks["pumpfun"] = pumpfun_data
            except Exception as e:
                logger.warning(f"Pump.fun error: {e}")
                tasks["pumpfun"] = None
                warnings.append(f"Pump.fun failed: {str(e)}")
            finally:
                progress.update(task, completed=True)
        
        # Solana Chain
        if "solana_chain" in clients:
            task = progress.add_task("Fetching data from Solana chain...", total=None)
            try:
                chain_data = await clients["solana_chain"].get_token_info(mint)
                if chain_data:
                    data_sources_used.append("solana_chain")
                tasks["solana_chain"] = chain_data
            except Exception as e:
                logger.warning(f"Solana chain error: {e}")
                tasks["solana_chain"] = None
                warnings.append(f"Solana chain failed: {str(e)}")
            finally:
                progress.update(task, completed=True)
    
    # Process and aggregate data
    task = progress.add_task("Processing data and calculating risk...", total=None)
    
    # Extract data from different sources
    pairs = []
    token_meta = None
    holders = []
    liquidity_lock = None
    trading_info = None
    pump_fun_info = None
    rugcheck_data = None
    
    # Process DEX Screener data
    if tasks.get("dexscreener"):
        dexscreener_data = tasks["dexscreener"]
        if "pairs" in dexscreener_data:
            pairs.extend(dexscreener_data["pairs"])
    
    # Process Birdeye data
    if tasks.get("birdeye"):
        birdeye_data = tasks["birdeye"]
        if "pools" in birdeye_data:
            # Convert pools to pairs format
            for pool in birdeye_data["pools"]:
                pairs.append({
                    "pair_address": pool.get("address", ""),
                    "base_token": pool.get("baseToken", {}),
                    "quote_token": pool.get("quoteToken", {}),
                    "liquidity_usd": pool.get("liquidity", {}).get("usd"),
                    "volume_24h_usd": pool.get("volume24h"),
                    "dex_id": pool.get("dexId", ""),
                })
    
    # Process Solana chain data
    if tasks.get("solana_chain"):
        chain_data = tasks["solana_chain"]
        if "holders" in chain_data:
            holders = chain_data["holders"]
        
        # Create basic token metadata
        if chain_data:
            token_meta = {
                "address": mint,
                "supply": chain_data.get("total_supply"),
                "mint_authority": None,  # Would need to decode mint account
                "freeze_authority": None,  # Would need to decode mint account
                "is_mint_authority_renounced": False,
                "is_freeze_authority_renounced": False,
            }
    
    # Process Pump.fun data
    if tasks.get("pumpfun"):
        pumpfun_data = tasks["pumpfun"]
        if "pump_fun_info" in pumpfun_data:
            pump_fun_info = pumpfun_data["pump_fun_info"]
    
    # Process RugCheck data
    if tasks.get("rugcheck"):
        rugcheck_data = tasks["rugcheck"]
        if "risk_summary" in rugcheck_data:
            rugcheck_data = rugcheck_data["risk_summary"]
    
    # Create basic trading info (would need more sophisticated analysis)
    trading_info = {
        "can_buy": True,
        "can_sell": True,
        "buy_tax_percentage": None,
        "sell_tax_percentage": None,
        "is_honeypot": False,
    }
    
    # Create basic liquidity lock info (would need more sophisticated analysis)
    liquidity_lock = {
        "is_locked": False,
        "locked_percentage": None,
        "lock_duration_days": None,
        "lock_provider": None,
        "lock_expiry": None,
    }
    
    # Generate risk report
    report = risk_scorer.assess_token_risk(
        mint_address=mint,
        token_meta=token_meta,
        pairs=pairs,
        holders=holders,
        liquidity_lock=liquidity_lock,
        trading_info=trading_info,
        pump_fun_info=pump_fun_info,
        rugcheck_data=rugcheck_data,
        data_sources_used=data_sources_used,
        warnings=warnings,
    )
    
    progress.update(task, completed=True)
    
    # Output results
    if json_output:
        output_json(report)
    else:
        output_console(report)


def output_json(report) -> None:
    """Output results in JSON format."""
    console.print(json.dumps(report.model_dump(), indent=2, default=str))


def output_console(report) -> None:
    """Output results in console format."""
    # Main verdict panel
    verdict_emoji = "✅" if report.overall_score <= 29 else "⚠️" if report.overall_score <= 59 else "❌"
    verdict_text = f"{verdict_emoji} {report.verdict}"
    
    verdict_panel = Panel(
        verdict_text,
        title="[bold]Safety Verdict[/bold]",
        subtitle=f"Risk Score: {report.overall_score}/100",
        border_style="green" if report.overall_score <= 29 else "yellow" if report.overall_score <= 59 else "red",
    )
    console.print(verdict_panel)
    
    # Risk details table
    risk_table = Table(title="Risk Assessment Details")
    risk_table.add_column("Rule", style="cyan")
    risk_table.add_column("Score", justify="right", style="magenta")
    risk_table.add_column("Severity", justify="center")
    risk_table.add_column("Message", style="white")
    
    for note in report.notes:
        severity_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(note.severity, "⚪")
        risk_table.add_row(
            note.rule_name,
            str(note.score),
            f"{severity_emoji} {note.severity.upper()}",
            note.message,
        )
    
    console.print(risk_table)
    
    # Token information
    if report.token_meta:
        info_table = Table(title="Token Information")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="white")
        
        info_table.add_row("Address", report.token_meta.address or "N/A")
        info_table.add_row("Supply", str(report.token_meta.supply) if report.token_meta.supply else "N/A")
        info_table.add_row("Mint Authority", "Renounced" if report.token_meta.is_mint_authority_renounced else "Active")
        info_table.add_row("Freeze Authority", "Renounced" if report.token_meta.is_freeze_authority_renounced else "Active")
        
        console.print(info_table)
    
    # Trading pairs
    if report.pairs:
        pairs_table = Table(title="Trading Pairs")
        pairs_table.add_column("DEX", style="cyan")
        pairs_table.add_column("Liquidity (USD)", justify="right", style="green")
        pairs_table.add_column("Volume 24h (USD)", justify="right", style="blue")
        pairs_table.add_column("Age", style="white")
        
        for pair in report.pairs[:5]:  # Show top 5 pairs
            liquidity = pair.liquidity_usd or 0
            volume = pair.volume_24h_usd or 0
            age = "N/A"
            if pair.pair_created_at:
                from datetime import datetime
                age_days = (datetime.now() - pair.pair_created_at).days
                age = f"{age_days} days"
            
            pairs_table.add_row(
                pair.dex_id or "Unknown",
                f"${liquidity:,.0f}" if liquidity else "N/A",
                f"${volume:,.0f}" if volume else "N/A",
                age,
            )
        
        console.print(pairs_table)
    
    # Top holders
    if report.top_holders:
        holders_table = Table(title="Top Holders")
        holders_table.add_column("Address", style="cyan")
        holders_table.add_column("Balance", justify="right", style="green")
        holders_table.add_column("Percentage", justify="right", style="blue")
        
        for holder in report.top_holders[:10]:  # Show top 10 holders
            balance = holder.balance or 0
            percentage = holder.percentage or 0
            holders_table.add_row(
                (holder.address or "N/A")[:8] + "...",
                f"{balance:,.0f}" if balance else "N/A",
                f"{percentage:.2f}%" if percentage else "N/A",
            )
        
        console.print(holders_table)
    
    # Warnings
    if report.warnings:
        warning_panel = Panel(
            "\n".join(f"• {warning}" for warning in report.warnings),
            title="[yellow]Warnings[/yellow]",
            border_style="yellow",
        )
        console.print(warning_panel)
    
    # Data sources
    sources_panel = Panel(
        ", ".join(report.data_sources_used) if report.data_sources_used else "None",
        title="[blue]Data Sources Used[/blue]",
        border_style="blue",
    )
    console.print(sources_panel)


async def fetch_all_data(mint: str, providers: List[str], fast: bool = False) -> dict:
    """
    Fetch data from all enabled providers.
    
    Args:
        mint: Token mint address
        providers: List of provider names to use
        fast: Whether to skip heavier calls
        
    Returns:
        Dictionary containing all fetched data
    """
    # Initialize clients
    clients = {
        "dexscreener": DexScreenerClient(),
        "birdeye": BirdeyeClient(),
        "rugcheck": RugCheckClient(),
        "pumpfun": PumpFunClient(),
        "solana_chain": SolanaChainClient(),
    }
    
    # Filter clients based on enabled providers
    clients = {k: v for k, v in clients.items() if k in providers}
    
    # Collect data from all sources
    tasks = {}
    data_sources_used = []
    warnings = []
    
    # DEX Screener
    if "dexscreener" in clients:
        try:
            dexscreener_data = await clients["dexscreener"].get_token_info(mint)
            if dexscreener_data:
                data_sources_used.append("dexscreener")
            tasks["dexscreener"] = dexscreener_data
        except Exception as e:
            logger.warning(f"DEX Screener error: {e}")
            tasks["dexscreener"] = None
            warnings.append(f"DEX Screener failed: {str(e)}")
    
    # Birdeye
    if "birdeye" in clients:
        try:
            birdeye_data = await clients["birdeye"].get_token_info(mint)
            if birdeye_data:
                data_sources_used.append("birdeye")
            tasks["birdeye"] = birdeye_data
        except Exception as e:
            logger.warning(f"Birdeye error: {e}")
            tasks["birdeye"] = None
            warnings.append(f"Birdeye failed: {str(e)}")
    
    # RugCheck
    if "rugcheck" in clients:
        try:
            rugcheck_data = await clients["rugcheck"].get_token_info(mint)
            if rugcheck_data:
                data_sources_used.append("rugcheck")
            tasks["rugcheck"] = rugcheck_data
        except Exception as e:
            logger.warning(f"RugCheck error: {e}")
            tasks["rugcheck"] = None
            warnings.append(f"RugCheck failed: {str(e)}")
    
    # Pump.fun
    if "pumpfun" in clients:
        try:
            pumpfun_data = await clients["pumpfun"].get_token_info(mint)
            if pumpfun_data:
                data_sources_used.append("pumpfun")
            tasks["pumpfun"] = pumpfun_data
        except Exception as e:
            logger.warning(f"Pump.fun error: {e}")
            tasks["pumpfun"] = None
            warnings.append(f"Pump.fun failed: {str(e)}")
    
    # Solana Chain
    if "solana_chain" in clients:
        try:
            chain_data = await clients["solana_chain"].get_token_info(mint)
            if chain_data:
                data_sources_used.append("solana_chain")
            tasks["solana_chain"] = chain_data
        except Exception as e:
            logger.warning(f"Solana chain error: {e}")
            tasks["solana_chain"] = None
            warnings.append(f"Solana chain failed: {str(e)}")
    
    # Process and aggregate data
    pairs = []
    token_meta = None
    holders = []
    liquidity_lock = None
    trading_info = None
    pump_fun_info = None
    rugcheck_data = None
    
    # Process DEX Screener data
    if tasks.get("dexscreener"):
        dexscreener_data = tasks["dexscreener"]
        if "pairs" in dexscreener_data:
            pairs.extend(dexscreener_data["pairs"])
    
    # Process Birdeye data
    if tasks.get("birdeye"):
        birdeye_data = tasks["birdeye"]
        if "pools" in birdeye_data:
            # Convert pools to pairs format
            for pool in birdeye_data["pools"]:
                pairs.append({
                    "pair_address": pool.get("address", ""),
                    "base_token": pool.get("baseToken", {}),
                    "quote_token": pool.get("quoteToken", {}),
                    "liquidity_usd": pool.get("liquidity", {}).get("usd"),
                    "volume_24h_usd": pool.get("volume24h"),
                    "dex_id": pool.get("dexId", ""),
                })
    
    # Process Solana chain data
    if tasks.get("solana_chain"):
        chain_data = tasks["solana_chain"]
        if "holders" in chain_data:
            holders = chain_data["holders"]
        if "token_meta" in chain_data:
            token_meta = chain_data["token_meta"]
        if "trading_info" in chain_data:
            trading_info = chain_data["trading_info"]
    
    # Process Pump.fun data
    if tasks.get("pumpfun"):
        pumpfun_data = tasks["pumpfun"]
        if "pump_fun_info" in pumpfun_data:
            pump_fun_info = pumpfun_data["pump_fun_info"]
    
    # Process RugCheck data
    if tasks.get("rugcheck"):
        rugcheck_data = tasks["rugcheck"]
    
    return {
        "mint_address": mint,
        "pairs": pairs,
        "token_meta": token_meta,
        "holders": holders,
        "liquidity_lock": liquidity_lock,
        "trading_info": trading_info,
        "pump_fun_info": pump_fun_info,
        "rugcheck_data": rugcheck_data,
        "data_sources_used": data_sources_used,
        "warnings": warnings,
    }


def assess_token_risk(data: dict) -> RiskReport:
    """
    Assess token risk based on collected data.
    
    Args:
        data: Dictionary containing all collected data
        
    Returns:
        RiskReport object with assessment results
    """
    risk_scorer = RiskScorer()
    return risk_scorer.assess_token_risk(
        mint_address=data["mint_address"],
        pairs=data["pairs"],
        token_meta=data["token_meta"],
        holders=data["holders"],
        liquidity_lock=data["liquidity_lock"],
        trading_info=data["trading_info"],
        pump_fun_info=data["pump_fun_info"],
        rugcheck_data=data["rugcheck_data"],
        data_sources_used=data["data_sources_used"],
        warnings=data["warnings"],
    )


if __name__ == "__main__":
    app()
