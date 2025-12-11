"""
Pension Data Analysis & Visualization
Analyzes pension fund data from data.gov.il

Usage:
    python pensia_analysis.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from pathlib import Path
from pensia_data import PensiaDataFetcher

# Configure matplotlib for Hebrew text support
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['figure.dpi'] = 100
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

# Use a clean style
sns.set_style("whitegrid")

# Color palette - modern and distinctive
COLORS = {
    'primary': '#2563eb',
    'secondary': '#7c3aed', 
    'success': '#059669',
    'warning': '#d97706',
    'danger': '#dc2626',
    'palette': ['#2563eb', '#7c3aed', '#059669', '#d97706', '#dc2626', '#0891b2', '#be185d', '#4f46e5']
}


def is_hebrew(text: str) -> bool:
    """Check if text contains Hebrew characters."""
    if not isinstance(text, str):
        return False
    hebrew_pattern = re.compile(r'[\u0590-\u05FF]')
    return bool(hebrew_pattern.search(text))


def reverse_hebrew(text: str) -> str:
    """
    Reverse Hebrew text for proper display in matplotlib.
    Handles mixed Hebrew/English text by reversing only Hebrew segments.
    """
    if not isinstance(text, str):
        return str(text)
    
    if not is_hebrew(text):
        return text
    
    # Split into segments of Hebrew and non-Hebrew
    # Hebrew Unicode range: \u0590-\u05FF
    segments = re.split(r'([\u0590-\u05FF\s]+)', text)
    
    result = []
    for segment in segments:
        if is_hebrew(segment):
            # Reverse Hebrew segment (including spaces within it)
            result.append(segment[::-1])
        else:
            result.append(segment)
    
    # Reverse the entire result for RTL display
    return ''.join(result[::-1])


def fix_hebrew_label(text: str, max_len: int = None) -> str:
    """
    Fix Hebrew text for matplotlib display.
    Optionally truncate to max_len characters.
    """
    if not isinstance(text, str):
        text = str(text)
    
    if max_len and len(text) > max_len:
        text = text[:max_len] + '...'
    
    return reverse_hebrew(text)


class PensiaAnalyzer:
    """Analyze and visualize pension fund data."""
    
    def __init__(self, df: pd.DataFrame = None):
        """
        Initialize analyzer with data.
        
        Args:
            df: DataFrame with pension data. If None, fetches from API.
        """
        if df is None:
            fetcher = PensiaDataFetcher()
            csv_path = Path("pensia_data.csv")
            
            if csv_path.exists():
                print("Loading data from CSV...")
                self.df = pd.read_csv(csv_path)
            else:
                print("Fetching data from API...")
                self.df = fetcher.to_dataframe()
                self.df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        else:
            self.df = df.copy()
        
        # Convert REPORT_PERIOD to datetime for easier analysis
        self.df['REPORT_DATE'] = pd.to_datetime(
            self.df['REPORT_PERIOD'].astype(str), 
            format='%Y%m'
        )
        
        print(f"Loaded {len(self.df):,} records")
    
    def summary_stats(self) -> dict:
        """Get summary statistics of the dataset."""
        df = self.df
        
        stats = {
            'total_records': len(df),
            'unique_funds': df['FUND_ID'].nunique(),
            'unique_managing_corps': df['MANAGING_CORPORATION'].nunique(),
            'date_range': (df['REPORT_DATE'].min(), df['REPORT_DATE'].max()),
            'years_covered': sorted(df['REPORTING_YEAR'].unique()),
            'fund_classifications': df['FUND_CLASSIFICATION'].unique().tolist(),
            'avg_monthly_yield': df['MONTHLY_YIELD'].mean(),
            'avg_management_fee': df['AVG_ANNUAL_MANAGEMENT_FEE'].mean(),
        }
        
        return stats
    
    def print_summary(self):
        """Print a formatted summary of the data."""
        stats = self.summary_stats()
        
        print("\n" + "=" * 60)
        print("📊 PENSION DATA SUMMARY")
        print("=" * 60)
        print(f"📁 Total Records: {stats['total_records']:,}")
        print(f"🏦 Unique Funds: {stats['unique_funds']}")
        print(f"🏢 Managing Corporations: {stats['unique_managing_corps']}")
        print(f"📅 Date Range: {stats['date_range'][0].strftime('%Y-%m')} to {stats['date_range'][1].strftime('%Y-%m')}")
        print(f"📈 Average Monthly Yield: {stats['avg_monthly_yield']:.2f}%")
        print(f"💰 Average Management Fee: {stats['avg_management_fee']:.2f}%")
        print(f"\n📋 Fund Classifications:")
        for clf in stats['fund_classifications']:
            count = len(self.df[self.df['FUND_CLASSIFICATION'] == clf])
            print(f"   • {clf}: {count:,} records")
    
    def top_funds_by_yield(self, n: int = 10, period: str = 'all') -> pd.DataFrame:
        """
        Get top performing funds by average yield.
        
        Args:
            n: Number of funds to return
            period: 'all', 'ytd', '3yr', or '5yr'
        """
        yield_col = {
            'all': 'MONTHLY_YIELD',
            'ytd': 'YEAR_TO_DATE_YIELD',
            '3yr': 'AVG_ANNUAL_YIELD_TRAILING_3YRS',
            '5yr': 'AVG_ANNUAL_YIELD_TRAILING_5YRS',
        }.get(period, 'MONTHLY_YIELD')
        
        result = (
            self.df.groupby(['FUND_ID', 'FUND_NAME', 'MANAGING_CORPORATION'])
            .agg({
                yield_col: 'mean',
                'TOTAL_ASSETS': 'last',
                'AVG_ANNUAL_MANAGEMENT_FEE': 'mean'
            })
            .reset_index()
            .dropna(subset=[yield_col])
            .sort_values(yield_col, ascending=False)
            .head(n)
        )
        
        result.columns = ['Fund ID', 'Fund Name', 'Manager', 'Avg Yield', 'Total Assets', 'Mgmt Fee']
        return result
    
    def top_funds_by_assets(self, n: int = 10) -> pd.DataFrame:
        """Get largest funds by total assets."""
        # Get latest data for each fund
        latest = self.df.sort_values('REPORT_DATE').groupby('FUND_ID').last().reset_index()
        
        result = (
            latest[['FUND_ID', 'FUND_NAME', 'MANAGING_CORPORATION', 'TOTAL_ASSETS', 
                   'AVG_ANNUAL_MANAGEMENT_FEE', 'MONTHLY_YIELD']]
            .sort_values('TOTAL_ASSETS', ascending=False)
            .head(n)
        )
        
        result.columns = ['Fund ID', 'Fund Name', 'Manager', 'Total Assets', 'Mgmt Fee', 'Monthly Yield']
        return result
    
    def lowest_fee_funds(self, n: int = 10, min_assets: float = 100) -> pd.DataFrame:
        """
        Get funds with lowest management fees.
        
        Args:
            n: Number of funds to return
            min_assets: Minimum assets to filter small funds
        """
        latest = self.df.sort_values('REPORT_DATE').groupby('FUND_ID').last().reset_index()
        
        result = (
            latest[latest['TOTAL_ASSETS'] >= min_assets]
            [['FUND_ID', 'FUND_NAME', 'MANAGING_CORPORATION', 'AVG_ANNUAL_MANAGEMENT_FEE',
              'TOTAL_ASSETS', 'MONTHLY_YIELD']]
            .sort_values('AVG_ANNUAL_MANAGEMENT_FEE')
            .head(n)
        )
        
        result.columns = ['Fund ID', 'Fund Name', 'Manager', 'Mgmt Fee', 'Total Assets', 'Monthly Yield']
        return result
    
    def fund_performance_over_time(self, fund_id: int) -> pd.DataFrame:
        """Get performance history for a specific fund."""
        return (
            self.df[self.df['FUND_ID'] == fund_id]
            .sort_values('REPORT_DATE')
            [['REPORT_DATE', 'FUND_NAME', 'MONTHLY_YIELD', 'YEAR_TO_DATE_YIELD', 
              'TOTAL_ASSETS', 'AVG_ANNUAL_MANAGEMENT_FEE']]
        )
    
    def compare_corporations(self) -> pd.DataFrame:
        """Compare performance across managing corporations."""
        return (
            self.df.groupby('MANAGING_CORPORATION')
            .agg({
                'FUND_ID': 'nunique',
                'TOTAL_ASSETS': 'sum',
                'MONTHLY_YIELD': 'mean',
                'AVG_ANNUAL_MANAGEMENT_FEE': 'mean',
            })
            .reset_index()
            .rename(columns={
                'MANAGING_CORPORATION': 'Corporation',
                'FUND_ID': 'Num Funds',
                'TOTAL_ASSETS': 'Total Assets',
                'MONTHLY_YIELD': 'Avg Monthly Yield',
                'AVG_ANNUAL_MANAGEMENT_FEE': 'Avg Mgmt Fee'
            })
            .sort_values('Total Assets', ascending=False)
        )
    
    # ==================== VISUALIZATION METHODS ====================
    
    def plot_yield_distribution(self, save_path: str = None):
        """Plot distribution of monthly yields."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Histogram
        data = self.df['MONTHLY_YIELD'].dropna()
        axes[0].hist(data, bins=50, color=COLORS['primary'], edgecolor='white', alpha=0.8)
        axes[0].axvline(data.mean(), color=COLORS['danger'], linestyle='--', linewidth=2, label=f'Mean: {data.mean():.2f}%')
        axes[0].axvline(data.median(), color=COLORS['success'], linestyle='--', linewidth=2, label=f'Median: {data.median():.2f}%')
        axes[0].set_xlabel('Monthly Yield (%)', fontsize=12)
        axes[0].set_ylabel('Frequency', fontsize=12)
        axes[0].set_title('Distribution of Monthly Yields', fontsize=14, fontweight='bold')
        axes[0].legend()
        
        # Box plot by year
        yearly_data = self.df[['REPORTING_YEAR', 'MONTHLY_YIELD']].dropna()
        yearly_data.boxplot(column='MONTHLY_YIELD', by='REPORTING_YEAR', ax=axes[1])
        axes[1].set_xlabel('Year', fontsize=12)
        axes[1].set_ylabel('Monthly Yield (%)', fontsize=12)
        axes[1].set_title('Monthly Yield by Year', fontsize=14, fontweight='bold')
        plt.suptitle('')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.show()
    
    def plot_top_funds(self, n: int = 15, save_path: str = None):
        """Plot top funds by assets and yield."""
        fig, axes = plt.subplots(1, 2, figsize=(16, 8))
        
        # Top by assets
        top_assets = self.top_funds_by_assets(n)
        colors = sns.color_palette(COLORS['palette'], n)
        
        bars1 = axes[0].barh(range(len(top_assets)), top_assets['Total Assets'], color=colors)
        axes[0].set_yticks(range(len(top_assets)))
        axes[0].set_yticklabels([fix_hebrew_label(name, 30) for name in top_assets['Fund Name']], fontsize=9)
        axes[0].set_xlabel('Total Assets (Millions)', fontsize=12)
        axes[0].set_title(f'Top {n} Funds by Total Assets', fontsize=14, fontweight='bold')
        axes[0].invert_yaxis()
        
        # Add value labels
        for i, (bar, val) in enumerate(zip(bars1, top_assets['Total Assets'])):
            axes[0].text(val + max(top_assets['Total Assets']) * 0.01, bar.get_y() + bar.get_height()/2,
                        f'{val:,.0f}', va='center', fontsize=8)
        
        # Top by yield
        top_yield = self.top_funds_by_yield(n)
        
        bars2 = axes[1].barh(range(len(top_yield)), top_yield['Avg Yield'], color=colors)
        axes[1].set_yticks(range(len(top_yield)))
        axes[1].set_yticklabels([fix_hebrew_label(name, 30) for name in top_yield['Fund Name']], fontsize=9)
        axes[1].set_xlabel('Average Monthly Yield (%)', fontsize=12)
        axes[1].set_title(f'Top {n} Funds by Average Yield', fontsize=14, fontweight='bold')
        axes[1].invert_yaxis()
        
        # Add value labels
        for bar, val in zip(bars2, top_yield['Avg Yield']):
            axes[1].text(val + max(top_yield['Avg Yield']) * 0.01, bar.get_y() + bar.get_height()/2,
                        f'{val:.2f}%', va='center', fontsize=8)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.show()
    
    def plot_fees_vs_yield(self, save_path: str = None):
        """Scatter plot of management fees vs yields."""
        # Get latest data per fund
        latest = self.df.sort_values('REPORT_DATE').groupby('FUND_ID').last().reset_index()
        latest = latest.dropna(subset=['AVG_ANNUAL_MANAGEMENT_FEE', 'MONTHLY_YIELD'])
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        scatter = ax.scatter(
            latest['AVG_ANNUAL_MANAGEMENT_FEE'],
            latest['MONTHLY_YIELD'],
            c=latest['TOTAL_ASSETS'],
            cmap='viridis',
            alpha=0.6,
            s=50,
            edgecolors='white',
            linewidth=0.5
        )
        
        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Total Assets', fontsize=11)
        
        # Add trend line
        z = pd.DataFrame({'fee': latest['AVG_ANNUAL_MANAGEMENT_FEE'], 
                          'yield': latest['MONTHLY_YIELD']}).dropna()
        if len(z) > 1:
            coef = z['fee'].corr(z['yield'])
            ax.annotate(f'Correlation: {coef:.3f}', xy=(0.05, 0.95), xycoords='axes fraction',
                       fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.set_xlabel('Annual Management Fee (%)', fontsize=12)
        ax.set_ylabel('Monthly Yield (%)', fontsize=12)
        ax.set_title('Management Fees vs Monthly Yield\n(Size = Total Assets)', fontsize=14, fontweight='bold')
        ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.show()
    
    def plot_market_trends(self, save_path: str = None):
        """Plot market-wide trends over time."""
        monthly = (
            self.df.groupby('REPORT_DATE')
            .agg({
                'MONTHLY_YIELD': 'mean',
                'TOTAL_ASSETS': 'sum',
                'FUND_ID': 'nunique',
                'AVG_ANNUAL_MANAGEMENT_FEE': 'mean'
            })
            .reset_index()
        )
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Average yield over time
        axes[0, 0].plot(monthly['REPORT_DATE'], monthly['MONTHLY_YIELD'], 
                        color=COLORS['primary'], linewidth=2)
        axes[0, 0].fill_between(monthly['REPORT_DATE'], monthly['MONTHLY_YIELD'], 
                                alpha=0.3, color=COLORS['primary'])
        axes[0, 0].axhline(0, color='gray', linestyle='--', alpha=0.5)
        axes[0, 0].set_title('Average Monthly Yield Over Time', fontsize=12, fontweight='bold')
        axes[0, 0].set_ylabel('Monthly Yield (%)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Total assets over time
        axes[0, 1].plot(monthly['REPORT_DATE'], monthly['TOTAL_ASSETS'] / 1000, 
                        color=COLORS['success'], linewidth=2)
        axes[0, 1].fill_between(monthly['REPORT_DATE'], monthly['TOTAL_ASSETS'] / 1000, 
                                alpha=0.3, color=COLORS['success'])
        axes[0, 1].set_title('Total Market Assets Over Time', fontsize=12, fontweight='bold')
        axes[0, 1].set_ylabel('Total Assets (Billions)')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Number of funds over time
        axes[1, 0].plot(monthly['REPORT_DATE'], monthly['FUND_ID'], 
                        color=COLORS['secondary'], linewidth=2)
        axes[1, 0].fill_between(monthly['REPORT_DATE'], monthly['FUND_ID'], 
                                alpha=0.3, color=COLORS['secondary'])
        axes[1, 0].set_title('Number of Active Funds Over Time', fontsize=12, fontweight='bold')
        axes[1, 0].set_ylabel('Number of Funds')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Average management fee over time
        axes[1, 1].plot(monthly['REPORT_DATE'], monthly['AVG_ANNUAL_MANAGEMENT_FEE'], 
                        color=COLORS['warning'], linewidth=2)
        axes[1, 1].fill_between(monthly['REPORT_DATE'], monthly['AVG_ANNUAL_MANAGEMENT_FEE'], 
                                alpha=0.3, color=COLORS['warning'])
        axes[1, 1].set_title('Average Management Fee Over Time', fontsize=12, fontweight='bold')
        axes[1, 1].set_ylabel('Management Fee (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.show()
    
    def plot_corporation_comparison(self, top_n: int = 10, save_path: str = None):
        """Compare top managing corporations."""
        corp_data = self.compare_corporations().head(top_n)
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        colors = sns.color_palette(COLORS['palette'], top_n)
        
        # Prepare Hebrew-fixed labels
        corp_labels = [fix_hebrew_label(name, 25) for name in corp_data['Corporation']]
        
        # Total Assets
        axes[0, 0].barh(range(len(corp_data)), corp_data['Total Assets'] / 1000, color=colors)
        axes[0, 0].set_yticks(range(len(corp_data)))
        axes[0, 0].set_yticklabels(corp_labels, fontsize=9)
        axes[0, 0].set_xlabel('Total Assets (Billions)')
        axes[0, 0].set_title('Total Assets by Corporation', fontsize=12, fontweight='bold')
        axes[0, 0].invert_yaxis()
        
        # Number of Funds
        axes[0, 1].barh(range(len(corp_data)), corp_data['Num Funds'], color=colors)
        axes[0, 1].set_yticks(range(len(corp_data)))
        axes[0, 1].set_yticklabels(corp_labels, fontsize=9)
        axes[0, 1].set_xlabel('Number of Funds')
        axes[0, 1].set_title('Number of Funds by Corporation', fontsize=12, fontweight='bold')
        axes[0, 1].invert_yaxis()
        
        # Average Yield
        axes[1, 0].barh(range(len(corp_data)), corp_data['Avg Monthly Yield'], color=colors)
        axes[1, 0].set_yticks(range(len(corp_data)))
        axes[1, 0].set_yticklabels(corp_labels, fontsize=9)
        axes[1, 0].set_xlabel('Average Monthly Yield (%)')
        axes[1, 0].set_title('Avg Monthly Yield by Corporation', fontsize=12, fontweight='bold')
        axes[1, 0].axvline(0, color='gray', linestyle='--', alpha=0.5)
        axes[1, 0].invert_yaxis()
        
        # Average Management Fee
        axes[1, 1].barh(range(len(corp_data)), corp_data['Avg Mgmt Fee'], color=colors)
        axes[1, 1].set_yticks(range(len(corp_data)))
        axes[1, 1].set_yticklabels(corp_labels, fontsize=9)
        axes[1, 1].set_xlabel('Average Management Fee (%)')
        axes[1, 1].set_title('Avg Management Fee by Corporation', fontsize=12, fontweight='bold')
        axes[1, 1].invert_yaxis()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.show()
    
    def plot_fund_history(self, fund_id: int, save_path: str = None):
        """Plot historical performance for a specific fund."""
        fund_data = self.fund_performance_over_time(fund_id)
        
        if fund_data.empty:
            print(f"No data found for fund ID: {fund_id}")
            return
        
        fund_name = fund_data['FUND_NAME'].iloc[0]
        fund_name_display = fix_hebrew_label(fund_name)
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'Fund Performance: {fund_name_display}', fontsize=14, fontweight='bold')
        
        # Monthly Yield
        axes[0, 0].plot(fund_data['REPORT_DATE'], fund_data['MONTHLY_YIELD'], 
                        color=COLORS['primary'], linewidth=2, marker='o', markersize=3)
        axes[0, 0].fill_between(fund_data['REPORT_DATE'], fund_data['MONTHLY_YIELD'], 
                                alpha=0.3, color=COLORS['primary'])
        axes[0, 0].axhline(0, color='gray', linestyle='--', alpha=0.5)
        axes[0, 0].set_title('Monthly Yield', fontsize=11)
        axes[0, 0].set_ylabel('Yield (%)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # YTD Yield
        axes[0, 1].plot(fund_data['REPORT_DATE'], fund_data['YEAR_TO_DATE_YIELD'], 
                        color=COLORS['success'], linewidth=2, marker='o', markersize=3)
        axes[0, 1].fill_between(fund_data['REPORT_DATE'], fund_data['YEAR_TO_DATE_YIELD'], 
                                alpha=0.3, color=COLORS['success'])
        axes[0, 1].axhline(0, color='gray', linestyle='--', alpha=0.5)
        axes[0, 1].set_title('Year-to-Date Yield', fontsize=11)
        axes[0, 1].set_ylabel('Yield (%)')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Total Assets
        axes[1, 0].plot(fund_data['REPORT_DATE'], fund_data['TOTAL_ASSETS'], 
                        color=COLORS['secondary'], linewidth=2, marker='o', markersize=3)
        axes[1, 0].fill_between(fund_data['REPORT_DATE'], fund_data['TOTAL_ASSETS'], 
                                alpha=0.3, color=COLORS['secondary'])
        axes[1, 0].set_title('Total Assets', fontsize=11)
        axes[1, 0].set_ylabel('Assets (Millions)')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Management Fee
        axes[1, 1].plot(fund_data['REPORT_DATE'], fund_data['AVG_ANNUAL_MANAGEMENT_FEE'], 
                        color=COLORS['warning'], linewidth=2, marker='o', markersize=3)
        axes[1, 1].set_title('Management Fee', fontsize=11)
        axes[1, 1].set_ylabel('Fee (%)')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.show()
    
    def generate_full_report(self, output_dir: str = "reports"):
        """Generate all visualizations and save to output directory."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print("\n🎨 Generating Full Analysis Report...")
        print("=" * 50)
        
        # Print summary
        self.print_summary()
        
        # Generate all plots
        print("\n📊 Generating visualizations...")
        
        self.plot_yield_distribution(save_path=output_path / "01_yield_distribution.png")
        self.plot_top_funds(save_path=output_path / "02_top_funds.png")
        self.plot_fees_vs_yield(save_path=output_path / "03_fees_vs_yield.png")
        self.plot_market_trends(save_path=output_path / "04_market_trends.png")
        self.plot_corporation_comparison(save_path=output_path / "05_corporation_comparison.png")
        
        # Save tables to CSV
        print("\n📋 Saving data tables...")
        
        self.top_funds_by_yield(20).to_csv(output_path / "top_funds_by_yield.csv", index=False)
        self.top_funds_by_assets(20).to_csv(output_path / "top_funds_by_assets.csv", index=False)
        self.lowest_fee_funds(20).to_csv(output_path / "lowest_fee_funds.csv", index=False)
        self.compare_corporations().to_csv(output_path / "corporation_comparison.csv", index=False)
        
        print(f"\n✅ Report generated in: {output_path.absolute()}")


def main():
    """Run the analysis."""
    analyzer = PensiaAnalyzer()
    
    # Print summary
    analyzer.print_summary()
    
    # Show top tables
    print("\n" + "=" * 60)
    print("🏆 TOP 10 FUNDS BY ASSETS")
    print("=" * 60)
    print(analyzer.top_funds_by_assets(10).to_string(index=False))
    
    print("\n" + "=" * 60)
    print("📈 TOP 10 FUNDS BY AVERAGE YIELD")
    print("=" * 60)
    print(analyzer.top_funds_by_yield(10).to_string(index=False))
    
    print("\n" + "=" * 60)
    print("💰 TOP 10 LOWEST FEE FUNDS (min 100M assets)")
    print("=" * 60)
    print(analyzer.lowest_fee_funds(10).to_string(index=False))
    
    # Generate visualizations
    print("\n" + "=" * 60)
    print("📊 GENERATING VISUALIZATIONS...")
    print("=" * 60)
    
    analyzer.plot_yield_distribution()
    analyzer.plot_top_funds()
    analyzer.plot_fees_vs_yield()
    analyzer.plot_market_trends()
    analyzer.plot_corporation_comparison()
    
    return analyzer


if __name__ == "__main__":
    analyzer = main()

