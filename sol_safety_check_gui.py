#!/usr/bin/env python3
"""
Solana Safety Checker - GUI Application
A desktop application for checking Solana token safety with a user-friendly interface.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import asyncio
import threading
import json
from datetime import datetime
import os
import sys

# Add the sol_safety_check module to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sol_safety_check.cli import fetch_all_data, assess_token_risk
from sol_safety_check.utils import validate_solana_address
from sol_safety_check.models import RiskReport


class SolSafetyCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Solana Safety Checker")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Variables
        self.token_address = tk.StringVar()
        self.use_fast_mode = tk.BooleanVar(value=True)
        self.selected_providers = {
            'dexscreener': tk.BooleanVar(value=True),
            'birdeye': tk.BooleanVar(value=True),
            'rugcheck': tk.BooleanVar(value=False),
            'pumpfun': tk.BooleanVar(value=True),
            'solana_chain': tk.BooleanVar(value=True)
        }
        
        self.setup_ui()
        self.load_env_config()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🔍 Solana Safety Checker", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Token Address Input
        ttk.Label(main_frame, text="Token Address:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.address_entry = ttk.Entry(main_frame, textvariable=self.token_address, width=50)
        self.address_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Quick buttons for common tokens
        quick_frame = ttk.Frame(main_frame)
        quick_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        ttk.Button(quick_frame, text="SOL", 
                  command=lambda: self.set_token("So11111111111111111111111111111111111111112")).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="USDC", 
                  command=lambda: self.set_token("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="Test Token", 
                  command=lambda: self.set_token("Fv73EXJBRfctJzLVC3P7uQP6er6JU8b4KtDr4LQFpump")).pack(side=tk.LEFT, padx=2)
        
        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Fast mode checkbox
        ttk.Checkbutton(options_frame, text="Fast Mode (skip heavy calls)", 
                       variable=self.use_fast_mode).grid(row=0, column=0, sticky=tk.W)
        
        # Data Sources Frame
        sources_frame = ttk.LabelFrame(main_frame, text="Data Sources", padding="10")
        sources_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Provider checkboxes
        providers = [
            ('DEX Screener (Free)', 'dexscreener'),
            ('Birdeye (API Key)', 'birdeye'),
            ('RugCheck (JWT)', 'rugcheck'),
            ('Pump.fun (API Key)', 'pumpfun'),
            ('Solana Chain (RPC)', 'solana_chain')
        ]
        
        for i, (label, key) in enumerate(providers):
            ttk.Checkbutton(sources_frame, text=label, 
                           variable=self.selected_providers[key]).grid(
                row=i//2, column=i%2, sticky=tk.W, padx=5, pady=2)
        
        # API Keys Frame
        api_frame = ttk.LabelFrame(main_frame, text="API Keys (Optional)", padding="10")
        api_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # API key entries
        self.api_keys = {}
        api_keys = [
            ('Birdeye API Key:', 'BIRDEYE_API_KEY'),
            ('RugCheck JWT:', 'RUGCHECK_JWT_TOKEN'),
            ('Moralis API Key:', 'MORALIS_API_KEY'),
            ('Bitquery API Key:', 'BITQUERY_API_KEY')
        ]
        
        for i, (label, key) in enumerate(api_keys):
            ttk.Label(api_frame, text=label).grid(row=i, column=0, sticky=tk.W, pady=2)
            self.api_keys[key] = tk.StringVar()
            ttk.Entry(api_frame, textvariable=self.api_keys[key], width=40, show="*").grid(
                row=i, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # Buttons Frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        # Analyze button
        self.analyze_button = ttk.Button(buttons_frame, text="🔍 Analyze Token", 
                                        command=self.analyze_token, style='Accent.TButton')
        self.analyze_button.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        ttk.Button(buttons_frame, text="Clear", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        
        # Save config button
        ttk.Button(buttons_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=5)
        
        # Results Frame
        results_frame = ttk.LabelFrame(main_frame, text="Analysis Results", padding="10")
        results_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results text area
        self.results_text = scrolledtext.ScrolledText(results_frame, height=15, width=80, 
                                                     font=('Courier', 10))
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def set_token(self, address):
        """Set token address in the entry field"""
        self.token_address.set(address)
    
    def load_env_config(self):
        """Load configuration from .env file"""
        try:
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key in self.api_keys:
                                self.api_keys[key].set(value)
        except Exception as e:
            print(f"Error loading .env file: {e}")
    
    def save_config(self):
        """Save configuration to .env file"""
        try:
            with open('.env', 'w') as f:
                f.write("# Solana Safety Checker Configuration\n")
                f.write(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for key, var in self.api_keys.items():
                    if var.get():
                        f.write(f"{key}={var.get()}\n")
                    else:
                        f.write(f"{key}=\n")
                
                f.write(f"\n# Other settings\n")
                f.write(f"SOLANA_RPC_URL=https://api.mainnet-beta.solana.com\n")
                f.write(f"MAX_REQUESTS_PER_MINUTE=60\n")
                f.write(f"REQUEST_TIMEOUT=30\n")
            
            messagebox.showinfo("Success", "Configuration saved to .env file!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def clear_results(self):
        """Clear the results text area"""
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Ready")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def analyze_token(self):
        """Analyze the token in a separate thread"""
        address = self.token_address.get().strip()
        
        if not address:
            messagebox.showerror("Error", "Please enter a token address")
            return
        
        if not validate_solana_address(address):
            messagebox.showerror("Error", "Invalid Solana address format")
            return
        
        # Disable analyze button during analysis
        self.analyze_button.config(state='disabled')
        self.update_status("Analyzing token...")
        
        # Run analysis in separate thread
        thread = threading.Thread(target=self.run_analysis, args=(address,))
        thread.daemon = True
        thread.start()
    
    def run_analysis(self, address):
        """Run the analysis (called from thread)"""
        try:
            # Update API keys in environment
            for key, var in self.api_keys.items():
                if var.get():
                    os.environ[key] = var.get()
            
            # Get selected providers
            providers = [key for key, var in self.selected_providers.items() if var.get()]
            
            if not providers:
                self.root.after(0, lambda: messagebox.showerror("Error", "Please select at least one data source"))
                return
            
            # Run analysis
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Fetch data
                self.root.after(0, lambda: self.update_status("Fetching data..."))
                data = loop.run_until_complete(fetch_all_data(address, providers, self.use_fast_mode.get()))
                
                # Assess risk
                self.root.after(0, lambda: self.update_status("Assessing risk..."))
                report = assess_token_risk(data)
                
                # Display results
                self.root.after(0, lambda: self.display_results(report))
                
            finally:
                loop.close()
                
        except Exception as e:
            self.root.after(0, lambda: self.handle_error(str(e)))
        finally:
            self.root.after(0, lambda: self.analyze_button.config(state='normal'))
            self.root.after(0, lambda: self.update_status("Ready"))
    
    def display_results(self, report: RiskReport):
        """Display analysis results"""
        self.results_text.delete(1.0, tk.END)
        
        # Format results
        result_text = f"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                SOLANA SAFETY CHECKER                                ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

Token Address: {report.mint_address}
Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                    SAFETY VERDICT                                    ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

{report.verdict}
Risk Score: {report.overall_score}/100

╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                 RISK ASSESSMENT                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

"""
        
        # Add risk details
        for note in report.notes:
            severity_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(note.severity, "⚪")
            result_text += f"{severity_emoji} {note.rule_name}: {note.message} (Score: {note.score})\n"
        
        result_text += f"\n"
        
        # Add token information
        if report.token_meta:
            result_text += f"╔══════════════════════════════════════════════════════════════════════════════════════╗\n"
            result_text += f"║                                TOKEN INFORMATION                                     ║\n"
            result_text += f"╚══════════════════════════════════════════════════════════════════════════════════════╝\n\n"
            result_text += f"Address: {report.token_meta.address or 'N/A'}\n"
            result_text += f"Supply: {report.token_meta.supply or 'N/A'}\n"
            result_text += f"Mint Authority: {'Renounced' if report.token_meta.is_mint_authority_renounced else 'Active'}\n"
            result_text += f"Freeze Authority: {'Renounced' if report.token_meta.is_freeze_authority_renounced else 'Active'}\n\n"
        
        # Add trading pairs
        if report.pairs:
            result_text += f"╔══════════════════════════════════════════════════════════════════════════════════════╗\n"
            result_text += f"║                                 TRADING PAIRS                                        ║\n"
            result_text += f"╚══════════════════════════════════════════════════════════════════════════════════════╝\n\n"
            for pair in report.pairs[:5]:
                liquidity = pair.liquidity_usd or 0
                volume = pair.volume_24h_usd or 0
                result_text += f"DEX: {pair.dex_id or 'Unknown'}\n"
                result_text += f"  Liquidity: ${liquidity:,.0f}\n"
                result_text += f"  Volume 24h: ${volume:,.0f}\n\n"
        
        # Add data sources
        result_text += f"Data Sources Used: {', '.join(report.data_sources_used)}\n"
        
        # Add warnings
        if report.warnings:
            result_text += f"\nWarnings:\n"
            for warning in report.warnings:
                result_text += f"⚠️  {warning}\n"
        
        self.results_text.insert(tk.END, result_text)
        self.results_text.see(tk.END)
    
    def handle_error(self, error_message):
        """Handle analysis errors"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"❌ Error: {error_message}\n\n")
        self.results_text.insert(tk.END, "Please check:\n")
        self.results_text.insert(tk.END, "• Token address is valid\n")
        self.results_text.insert(tk.END, "• Internet connection is working\n")
        self.results_text.insert(tk.END, "• API keys are correct (if using paid services)\n")
        self.results_text.insert(tk.END, "• At least one data source is selected\n")


def main():
    """Main function to run the GUI application"""
    root = tk.Tk()
    app = SolSafetyCheckerGUI(root)
    
    # Center the window
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()


if __name__ == "__main__":
    main()
