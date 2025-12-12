# 📊 Pension Funds Explorer

Interactive dashboard for Israeli pension fund data from [data.gov.il](https://data.gov.il).

## 🚀 Installation

### Prerequisites

1. **Install Python 3.9+**
   - Download from [python.org/downloads](https://www.python.org/downloads/)
   - ⚠️ **Windows:** Check ✅ **"Add Python to PATH"** during installation

2. **Install Git**
   - Windows: [git-scm.com/download/win](https://git-scm.com/download/win)
   - Mac: `xcode-select --install`
   - Linux: `sudo apt install git`

### Clone & Run

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/birmanet.git
cd birmanet

# Install dependencies (first time only)
pip install -r requirements.txt

# Run the app
streamlit run pensia_app.py
```

### Windows Quick Start

After cloning, just **double-click `run_app.bat`** - it handles everything automatically!

### Mac/Linux Quick Start

```bash
chmod +x run_app.sh
./run_app.sh
```

## 🔄 Updating

```bash
cd birmanet
git pull
```

Then run the app again.

## 📋 Features

### 📋 Data Table Tab
- View all pension funds for any report period
- Sort by any column (YTD Yield, Monthly Yield, Assets, etc.)
- Filter by classification, corporation, exposure levels
- Download data as CSV
- Dynamic chart showing top 5 funds performance

### 📊 Charts Tab
- Top funds by yield and assets
- Yield vs Fee scatter plot
- Yield distribution histogram
- Classification breakdown

### ⚖️ Compare Funds Tab
- Side-by-side comparison of up to 5 funds
- Historical performance charts

### 📈 Historical Trends Tab
- Detailed history for any single fund
- Statistics summary (min, max, avg, std dev)

## 🔧 Sidebar Filters

| Filter | Description |
|--------|-------------|
| 📅 Report Period | Select month/year |
| 📁 Fund Classification | Filter by fund type |
| 🏢 Managing Corporation | Filter by company |
| 💰 Minimum Total Assets | Filter small funds |
| 📊 Stock Market Exposure | 0-100% range |
| 🌍 Foreign Exposure | 0-100% range |
| 💱 Foreign Currency Exposure | 0-100% range |
| 🔍 Search | Find funds by name |

## 💾 Data Caching

- Data is cached locally in `pension_cache.db` (SQLite)
- Cache expires after 24 hours
- Click **🔄 Refresh Data** to force update
- Cache age shown in sidebar

## 📁 Project Files

| File | Description |
|------|-------------|
| `pensia_app.py` | Main Streamlit dashboard |
| `pensia_data.py` | API client for data.gov.il |
| `pensia_analysis.py` | Analysis & visualization module |
| `requirements.txt` | Python dependencies |
| `run_app.bat` | Windows launcher |
| `run_app.sh` | Mac/Linux launcher |
| `pension_cache.db` | Local data cache (auto-generated) |

## 📊 Data Source

Data is fetched from Israel's open data portal:
- Website: [data.gov.il](https://data.gov.il)
- Dataset: Pension fund net data (pensia-net)
- Resources:
  - 2024-2025: `6d47d6b5-cb08-488b-b333-f1e717b1e1bd`
  - 2023: `4694d5a7-5284-4f3d-a2cb-5887f43fb55e`

## 🛠️ Troubleshooting

### "Python is not recognized"
- Reinstall Python and check ✅ "Add Python to PATH"
- Or manually add Python to your system PATH

### "streamlit is not recognized"
```bash
pip install streamlit
```

### App won't start
```bash
pip install -r requirements.txt --force-reinstall
```

### Data not loading
- Check your internet connection
- Click 🔄 Refresh Data
- Delete `pension_cache.db` and restart

## 📝 License

MIT License - feel free to use and modify.
