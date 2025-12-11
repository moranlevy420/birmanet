# 📊 Pension Funds Explorer

Interactive dashboard for Israeli pension fund data from [data.gov.il](https://data.gov.il).

## 🚀 Quick Start

### Windows
1. Install Python from [python.org](https://www.python.org/downloads/) (check "Add Python to PATH")
2. Double-click `run_app.bat`
3. The browser will open automatically

### Mac/Linux
1. Install Python 3 if not already installed
2. Open terminal in this folder
3. Run: `chmod +x run_app.sh && ./run_app.sh`

### Manual Start
```bash
pip install -r requirements.txt
streamlit run pensia_app.py
```

## 📋 Features

### Data Table Tab
- View all pension funds for any report period
- Sort by any column (YTD Yield, Monthly Yield, Assets, etc.)
- Filter by classification, corporation, exposure levels
- Download data as CSV
- Dynamic chart showing top 5 funds performance

### Charts Tab
- Top funds by yield and assets
- Yield vs Fee scatter plot
- Yield distribution histogram
- Classification breakdown

### Compare Funds Tab
- Side-by-side comparison of up to 5 funds
- Historical performance charts

### Historical Trends Tab
- Detailed history for any single fund
- Statistics summary

## 🔧 Sidebar Filters

- **Report Period** - Select month/year
- **Fund Classification** - Filter by fund type
- **Managing Corporation** - Filter by company
- **Minimum Total Assets** - Filter small funds
- **Stock Market Exposure** - 0-100% range
- **Foreign Exposure** - 0-100% range
- **Foreign Currency Exposure** - 0-100% range
- **Search** - Find funds by name

## 📁 Files

| File | Description |
|------|-------------|
| `pensia_app.py` | Main Streamlit dashboard |
| `pensia_data.py` | API client for data.gov.il |
| `pensia_analysis.py` | Analysis & visualization module |
| `requirements.txt` | Python dependencies |
| `run_app.bat` | Windows launcher |
| `run_app.sh` | Mac/Linux launcher |

## 📊 Data Source

Data is fetched from Israel's open data portal:
- [data.gov.il](https://data.gov.il)
- Pension fund net data (pensia-net)

## 🔄 Refresh Data

Click the "🔄 Refresh Data" button in the sidebar to fetch the latest data from the API.

# birmanet
