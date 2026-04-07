"""
Web Scraper — fetches live financial data from official Indian sources
Sources: RBI, NSE, AMFI (mutual fund NAV), MCX (gold/silver)
"""
import logging
import requests
import json
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}
TIMEOUT = 15


class FinancialScraper:

    def scrape_all(self) -> List[dict]:
        """Run all scrapers and return list of docs for RAG ingestion."""
        scrapers = [
            ("RBI Policy Rates", self.scrape_rbi_rates),
            ("NSE Indices", self.scrape_nse_indices),
            ("AMFI Mutual Funds", self.scrape_amfi_nav),
            ("Bank FD Rates", self.scrape_fd_rates),
            ("Gold & Silver Prices", self.scrape_commodity_prices),
        ]
        docs = []
        for name, fn in scrapers:
            try:
                result = fn()
                if result:
                    docs.append(result)
                    logger.info(f"Scraped: {name} ({len(result.get('text',''))} chars)")
            except Exception as e:
                logger.error(f"Scrape failed [{name}]: {e}")
        return docs

    # ── RBI Key Policy Rates ──────────────────────────────────

    def scrape_rbi_rates(self) -> Optional[dict]:
        """Scrape RBI key rates from official page."""
        url = "https://www.rbi.org.in/Scripts/BS_ViewBulletin.aspx"
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            soup = BeautifulSoup(r.text, "html.parser")
            # Extract tables with rate info
            tables = soup.find_all("table")
            text_parts = [f"RBI Key Policy Rates — Scraped {datetime.now().strftime('%d %b %Y')}\n"]
            for table in tables[:5]:
                rows = table.find_all("tr")
                for row in rows:
                    cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
                    if cells and any(kw in " ".join(cells).lower() for kw in ["repo", "rate", "crr", "slr", "percent"]):
                        text_parts.append(" | ".join(cells))
            if len(text_parts) < 3:
                raise ValueError("Too little data extracted")
            return {
                "text": "\n".join(text_parts),
                "source": "RBI Official",
                "metadata": {"type": "policy_rates", "scraped_at": datetime.utcnow().isoformat()}
            }
        except Exception:
            # Return curated fallback data (updated periodically)
            return self._rbi_fallback()

    def _rbi_fallback(self) -> dict:
        text = """RBI Key Policy Rates (Latest Available Data)
Repo Rate: 6.50% per annum
Reverse Repo Rate: 3.35% per annum
Marginal Standing Facility (MSF) Rate: 6.75% per annum
Bank Rate: 6.75% per annum
Cash Reserve Ratio (CRR): 4.00%
Statutory Liquidity Ratio (SLR): 18.00%

These rates govern interbank lending and directly influence home loan EMIs, FD rates, and savings account interest.
When Repo Rate increases, home loan EMIs rise and FD rates tend to improve.
When Repo Rate decreases, loans become cheaper but savings returns fall.
Source: Reserve Bank of India — rbi.org.in"""
        return {"text": text, "source": "RBI Fallback Data", "metadata": {"type": "policy_rates"}}

    # ── NSE Market Indices ────────────────────────────────────

    def scrape_nse_indices(self) -> Optional[dict]:
        try:
            # NSE provides JSON API for indices
            session = requests.Session()
            session.get("https://www.nseindia.com", headers=HEADERS, timeout=TIMEOUT)
            r = session.get(
                "https://www.nseindia.com/api/allIndices",
                headers={**HEADERS, "Referer": "https://www.nseindia.com/"},
                timeout=TIMEOUT
            )
            data = r.json()
            lines = [f"NSE Market Data — {datetime.now().strftime('%d %b %Y %H:%M IST')}\n"]
            key_indices = ["NIFTY 50", "NIFTY BANK", "NIFTY MIDCAP 100", "NIFTY SMALLCAP 100",
                           "NIFTY IT", "INDIA VIX", "NIFTY AUTO", "NIFTY PHARMA"]
            for item in data.get("data", []):
                name = item.get("indexSymbol", "")
                if name in key_indices:
                    lines.append(
                        f"{name}: {item.get('last', 'N/A')} | "
                        f"Change: {item.get('change', 'N/A')} ({item.get('percentChange', 'N/A')}%) | "
                        f"52w High: {item.get('yearHigh', 'N/A')} | 52w Low: {item.get('yearLow', 'N/A')}"
                    )
            return {
                "text": "\n".join(lines),
                "source": "NSE India",
                "metadata": {"type": "market_indices", "scraped_at": datetime.utcnow().isoformat()}
            }
        except Exception as e:
            logger.warning(f"NSE scrape failed: {e}")
            return self._nse_fallback()

    def _nse_fallback(self) -> dict:
        text = """NSE Market Indices (Reference Data)
Nifty 50: ~22,500 (approx — fetch live data for current value)
Nifty Bank: ~48,000
Nifty Midcap 100: ~50,000
Nifty IT: ~35,000
India VIX (Volatility): ~14 (below 15 = low volatility = good for SIPs)

Key insight: Nifty 50 has given ~12-14% CAGR over last 10 years.
SIP in Nifty 50 index funds has beaten most actively managed funds over long term.
Current PE ratio of Nifty 50 is around 20-22x which is fairly valued.
Source: NSE India — nseindia.com"""
        return {"text": text, "source": "NSE Fallback", "metadata": {"type": "market_indices"}}

    # ── AMFI Mutual Fund NAVs ─────────────────────────────────

    def scrape_amfi_nav(self) -> Optional[dict]:
        """AMFI provides a flat text file with all mutual fund NAVs."""
        try:
            r = requests.get(
                "https://www.amfiindia.com/spages/NAVAll.txt",
                headers=HEADERS, timeout=30
            )
            lines = r.text.strip().split("\n")
            # Parse the AMFI format: Scheme Code;ISIN;ISIN2;Scheme Name;NAV Date;NAV
            popular_funds = [
                "SBI Blue Chip", "HDFC Top 100", "Mirae Asset Large Cap",
                "Axis Bluechip", "Parag Parikh Flexi Cap", "SBI Small Cap",
                "Nippon India Small Cap", "HDFC Mid-Cap Opportunities",
                "Axis Elss Tax Saver", "SBI Magnum ELSS",
                "HDFC Liquid Fund", "Parag Parikh Liquid Fund",
                "SBI Overnight Fund", "Mirae Asset Overnight Fund",
                "SBI Nifty Index", "UTI Nifty 50 Index",
            ]
            selected = []
            for line in lines:
                parts = line.split(";")
                if len(parts) >= 6:
                    name = parts[3].strip()
                    nav = parts[4].strip()
                    date = parts[5].strip() if len(parts) > 5 else ""
                    for keyword in popular_funds:
                        if keyword.lower() in name.lower():
                            selected.append(f"{name}: NAV ₹{nav} (as of {date})")
                            break
            text = f"AMFI Mutual Fund NAVs — {datetime.now().strftime('%d %b %Y')}\n"
            text += "\n".join(selected[:40]) if selected else "NAV data not available"
            text += "\n\nNote: Invest via SEBI-registered platforms: Zerodha Coin, MFCentral, Groww, ET Money."
            return {
                "text": text,
                "source": "AMFI India",
                "metadata": {"type": "mutual_fund_nav", "scraped_at": datetime.utcnow().isoformat()}
            }
        except Exception as e:
            logger.warning(f"AMFI scrape failed: {e}")
            return self._amfi_fallback()

    def _amfi_fallback(self) -> dict:
        text = """Popular Mutual Funds — Reference Data (verify current NAV on amfiindia.com)

LARGE CAP FUNDS (Low-Moderate Risk, 10-13% expected CAGR):
- SBI Blue Chip Fund: Historically strong performer, good for conservative equity investors
- Mirae Asset Large Cap Fund: Consistent top quartile performance
- HDFC Top 100 Fund: Large AUM, value-style investing

FLEXI CAP FUNDS (Moderate Risk, 12-15% expected CAGR):
- Parag Parikh Flexi Cap: International diversification + India exposure. Excellent long-term track record
- HDFC Flexi Cap Fund: Good multi-cap allocation

ELSS FUNDS (Tax saving under 80C, 3-year lock-in, 12-16% expected CAGR):
- Axis ELSS Tax Saver: Consistent performer
- SBI Magnum ELSS: Large AUM, stable
- Mirae Asset ELSS: Growth-oriented

SMALL CAP FUNDS (High Risk, 15-20% expected CAGR over 7+ years):
- SBI Small Cap Fund: Top performer but closed for lumpsum
- Nippon India Small Cap: Large AUM small cap fund

LIQUID/DEBT FUNDS (Low Risk, 6-7.5% expected return):
- SBI Liquid Fund: For emergency corpus
- Parag Parikh Liquid Fund: Ethical, low cost
Source: AMFI India — amfiindia.com"""
        return {"text": text, "source": "AMFI Fallback", "metadata": {"type": "mutual_fund_nav"}}

    # ── Bank FD Rates ─────────────────────────────────────────

    def scrape_fd_rates(self) -> dict:
        """Curated FD rates — these change slowly, updated manually."""
        text = """Bank Fixed Deposit Interest Rates (2024-25)

STATE BANK OF INDIA (SBI):
- 7 days to 45 days: 3.00%
- 46 days to 179 days: 4.50%
- 180 days to 210 days: 5.75%
- 211 days to less than 1 year: 6.00%
- 1 year to less than 2 years: 6.80%
- 2 years to less than 3 years: 7.00%
- 3 years to less than 5 years: 6.75%
- 5 years and up to 10 years: 6.50%
Senior Citizen: Additional 0.50% on all tenures
Special: SBI Amrit Kalash (400 days): 7.10%

HDFC BANK:
- 1 year: 6.60%
- 15 months: 7.10%
- 2 years: 7.00%
- 3-5 years: 7.00%
Senior Citizen: Additional 0.50-0.75%

ICICI BANK:
- 1 year: 6.70%
- 390 days (iMobile special): 7.25%
- 2-3 years: 7.00%

AXIS BANK:
- 1 year: 6.70%
- 18 months: 7.10%

SMALL FINANCE BANKS (Higher rates, insured up to ₹5L by DICGC):
- Suryoday SFB: Up to 9.10% (5 years)
- Unity SFB: Up to 9.00%
- ESAF SFB: Up to 8.75%

TDS on FD: 10% if interest > ₹40,000/year (₹50,000 for senior citizens). 
Submit Form 15G/15H if total income below taxable limit to avoid TDS.
FD interest is taxable as per income slab — not tax efficient for high earners (30% slab).
Prefer ELSS or SGB for tax efficiency.
Source: Bank websites (January 2025)"""
        return {"text": text, "source": "Bank FD Rates", "metadata": {"type": "fd_rates"}}

    # ── Gold & Silver Commodity Prices ────────────────────────

    def scrape_commodity_prices(self) -> dict:
        """Try to get gold price from a public API, fallback to reference data."""
        try:
            r = requests.get(
                "https://api.metals.live/v1/spot/gold,silver",
                timeout=TIMEOUT, headers=HEADERS
            )
            data = r.json()
            gold_usd = data[0].get("price", 2300) if data else 2300
            silver_usd = data[1].get("price", 27) if len(data) > 1 else 27
            # USD to INR (approx)
            usd_inr = 83.5
            gold_inr_10g = gold_usd * usd_inr * 10 / 31.1035
            silver_inr_kg = silver_usd * usd_inr * 1000 / 31.1035
            text = f"""Gold & Silver Prices — {datetime.now().strftime('%d %b %Y')}
Gold (MCX): ₹{gold_inr_10g:,.0f} per 10 grams (approx, based on international spot + INR rate)
Silver (MCX): ₹{silver_inr_kg:,.0f} per kg

Gold investment options:
1. Sovereign Gold Bond (SGB): Best option — 2.5% annual interest + gold appreciation. No GST. No capital gains if held to maturity (8 years).
2. Gold ETF: Like buying gold in demat form. Tracks MCX gold. 1% expense ratio approx.
3. Digital Gold: Buy from Groww, PhonePe, Paytm. No GST on buy. Liquid.
4. Physical Gold: 3% GST + making charges. Not recommended for pure investment.

Historical performance: Gold has given ~8% CAGR in INR over 10 years.
Recommended allocation: 10-15% of portfolio for middle/upper class investors.
Source: metals.live + MCX reference"""
        except Exception:
            text = """Gold & Silver Reference Prices (2025)
Gold (MCX): Approximately ₹72,000-75,000 per 10 grams
Silver (MCX): Approximately ₹85,000-90,000 per kg

Investment recommendation: Sovereign Gold Bonds (SGBs) are the best way to invest in gold:
- 2.5% annual interest (paid semi-annually) + gold price appreciation
- Zero capital gains tax if held to maturity (8 years)
- Issued by RBI, backed by Government of India
- Minimum 1 gram, Maximum 4 kg per financial year per individual

Gold has historically acted as an inflation hedge and safe haven during market downturns.
Source: MCX India / RBI SGB data"""
        return {"text": text, "source": "Commodity Prices", "metadata": {"type": "commodity_prices"}}
