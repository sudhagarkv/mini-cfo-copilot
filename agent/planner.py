import re
import pandas as pd
from typing import Tuple, Dict, Optional, List
from . import metrics
from .data import load_csvs

MONTH_RE = r"(?P<month>(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})"
YEAR_RE = r"(?P<year>\d{4})"

def parse_month(text: str) -> Optional[pd.Timestamp]:
    m = re.search(MONTH_RE, text, flags=re.IGNORECASE)
    if not m:
        return None
    return pd.to_datetime(m.group("month"))

def parse_year(text: str) -> Optional[int]:
    m = re.search(YEAR_RE, text)
    if not m:
        return None
    return int(m.group("year"))

def get_latest_month() -> pd.Timestamp:
    a, _, _, _ = load_csvs()
    return pd.to_datetime(a["month"].max())

def extract_time_period(question: str) -> Dict[str, any]:
    """Extract time period info from question"""
    q = question.lower()
    result = {"months": None, "year": None, "specific_month": None, "last_n": None}
    
    # Specific month
    result["specific_month"] = parse_month(question)
    
    # Year
    result["year"] = parse_year(question)
    
    # Last N months/periods
    if "last 3" in q or "last three" in q or "3 months" in q:
        result["last_n"] = 3
    elif "last 6" in q or "last six" in q or "6 months" in q:
        result["last_n"] = 6
    elif "last 12" in q or "last twelve" in q or "12 months" in q or "year" in q:
        result["last_n"] = 12
    elif "ytd" in q or "year to date" in q:
        current_year = get_latest_month().year
        result["year"] = current_year
    
    return result

def plan_and_run(question: str) -> Tuple[str, Dict, str]:
    q = question.lower()
    time_info = extract_time_period(question)
    
    # Revenue questions
    if "revenue" in q:
        if "budget" in q or "vs" in q or "versus" in q or "compared" in q:
            # Revenue vs Budget
            mth = time_info["specific_month"] or get_latest_month()
            res = metrics.revenue_vs_budget(mth)
            text = f"{mth.strftime('%B %Y')} Revenue vs Budget: Actual ${res['actual_usd']:,.0f}, Budget ${res['budget_usd']:,.0f}, Variance ${res['variance_usd']:,.0f} ({res['variance_pct']:.1f}%)."
            return "revenue_vs_budget", res, text
        elif "trend" in q or "over time" in q or "monthly" in q:
            # Revenue trend
            return handle_revenue_trend(time_info)
        else:
            # Simple revenue query
            return handle_revenue_query(time_info)
    
    # Gross Margin questions
    if "gross margin" in q or "gm" in q or "margin" in q:
        last_n = time_info["last_n"] or (12 if "trend" in q else None)
        df = metrics.gross_margin_series(last_n)
        period_desc = f" (last {last_n} months)" if last_n else ""
        text = f"Gross Margin % trend{period_desc}."
        return "gross_margin_trend", {"series": df.to_dict(orient="list")}, text
    
    # COGS questions
    if "cogs" in q or "cost of goods" in q:
        return handle_cogs_query(time_info)
    
    # Opex questions
    if "opex" in q or "operating expense" in q or "operational expense" in q:
        if "breakdown" in q or "by category" in q or "categories" in q:
            mth = time_info["specific_month"] or get_latest_month()
            df = metrics.opex_breakdown(mth)
            text = f"Opex breakdown for {mth.strftime('%B %Y')} by category."
            return "opex_breakdown", {"table": df.to_dict(orient="records"), "month": mth.isoformat()}, text
        else:
            return handle_opex_query(time_info)
    
    # EBITDA questions
    if "ebitda" in q or "earnings" in q:
        return handle_ebitda_query(time_info)
    
    # Cash questions
    if "cash" in q:
        if "runway" in q:
            res = metrics.cash_runway_months()
            mth = pd.to_datetime(res["reference_month"])
            months = res["runway_months"]
            text = f"Cash runway as of {mth.strftime('%B %Y')}: ${res['cash_usd']:,.0f} cash; avg burn ${res['avg_monthly_burn_usd']:,.0f}/mo -> runway {months:.1f} months."
            return "cash_runway", res, text
        else:
            return handle_cash_query(time_info)
    
    # Performance questions
    if "performance" in q or "how are we doing" in q or "summary" in q or "overview" in q:
        return handle_performance_summary(time_info)
    
    # Comparison questions
    if "compare" in q or "comparison" in q or "vs" in q or "versus" in q:
        return handle_comparison_query(question, time_info)
    
    # Growth questions
    if "growth" in q or "growing" in q or "increase" in q or "decrease" in q:
        return handle_growth_query(question, time_info)
    
    # Try to infer from any financial terms
    return handle_general_financial_query(question, time_info)

def handle_revenue_trend(time_info: Dict) -> Tuple[str, Dict, str]:
    """Handle revenue trend questions"""
    from .data import to_usd
    a, _, fx, _ = load_csvs()
    actuals_usd = to_usd(a, fx)
    
    rev_data = actuals_usd[actuals_usd["account_category"] == "Revenue"]
    monthly_rev = rev_data.groupby("month")["amount_usd"].sum().reset_index()
    monthly_rev = monthly_rev.sort_values("month")
    
    if time_info["last_n"]:
        monthly_rev = monthly_rev.tail(time_info["last_n"])
    elif time_info["year"]:
        monthly_rev = monthly_rev[monthly_rev["month"].dt.year == time_info["year"]]
    
    text = f"Revenue trend over {len(monthly_rev)} months."
    return "revenue_trend", {"series": monthly_rev.to_dict(orient="list")}, text

def handle_revenue_query(time_info: Dict) -> Tuple[str, Dict, str]:
    """Handle simple revenue questions"""
    from .data import to_usd
    a, _, fx, _ = load_csvs()
    actuals_usd = to_usd(a, fx)
    
    if time_info["specific_month"]:
        mth = time_info["specific_month"]
        rev = actuals_usd[(actuals_usd["month"] == mth) & (actuals_usd["account_category"] == "Revenue")]["amount_usd"].sum()
        text = f"{mth.strftime('%B %Y')} Revenue: ${rev:,.0f}"
        return "simple_metric", {"value": float(rev), "month": mth.isoformat()}, text
    else:
        latest = get_latest_month()
        rev = actuals_usd[(actuals_usd["month"] == latest) & (actuals_usd["account_category"] == "Revenue")]["amount_usd"].sum()
        text = f"Latest Revenue ({latest.strftime('%B %Y')}): ${rev:,.0f}"
        return "simple_metric", {"value": float(rev), "month": latest.isoformat()}, text

def handle_cogs_query(time_info: Dict) -> Tuple[str, Dict, str]:
    """Handle COGS questions"""
    from .data import to_usd
    a, _, fx, _ = load_csvs()
    actuals_usd = to_usd(a, fx)
    
    mth = time_info["specific_month"] or get_latest_month()
    cogs = actuals_usd[(actuals_usd["month"] == mth) & (actuals_usd["account_category"] == "COGS")]["amount_usd"].sum()
    text = f"{mth.strftime('%B %Y')} COGS: ${cogs:,.0f}"
    return "simple_metric", {"value": float(cogs), "month": mth.isoformat()}, text

def handle_opex_query(time_info: Dict) -> Tuple[str, Dict, str]:
    """Handle general Opex questions"""
    from .data import to_usd
    a, _, fx, _ = load_csvs()
    actuals_usd = to_usd(a, fx)
    
    mth = time_info["specific_month"] or get_latest_month()
    opex = actuals_usd[(actuals_usd["month"] == mth) & (actuals_usd["account_category"].str.startswith("Opex:"))]["amount_usd"].sum()
    text = f"{mth.strftime('%B %Y')} Total Opex: ${opex:,.0f}"
    return "simple_metric", {"value": float(opex), "month": mth.isoformat()}, text

def handle_ebitda_query(time_info: Dict) -> Tuple[str, Dict, str]:
    """Handle EBITDA questions"""
    ebitda_df = metrics.ebitda_series().sort_values("month")
    
    if time_info["specific_month"]:
        mth = time_info["specific_month"]
        ebitda_val = ebitda_df[ebitda_df["month"] == mth]["ebitda_usd"].iloc[0] if len(ebitda_df[ebitda_df["month"] == mth]) > 0 else 0
        text = f"{mth.strftime('%B %Y')} EBITDA: ${ebitda_val:,.0f}"
        return "simple_metric", {"value": float(ebitda_val), "month": mth.isoformat()}, text
    elif time_info["last_n"]:
        recent = ebitda_df.tail(time_info["last_n"])
        text = f"EBITDA trend (last {time_info['last_n']} months)"
        return "ebitda_trend", {"series": recent.to_dict(orient="list")}, text
    else:
        latest = ebitda_df.iloc[-1]
        text = f"Latest EBITDA ({pd.to_datetime(latest['month']).strftime('%B %Y')}): ${latest['ebitda_usd']:,.0f}"
        return "simple_metric", {"value": float(latest['ebitda_usd']), "month": latest['month']}, text

def handle_cash_query(time_info: Dict) -> Tuple[str, Dict, str]:
    """Handle cash balance questions"""
    _, _, _, cash = load_csvs()
    
    mth = time_info["specific_month"] or pd.to_datetime(cash["month"].max())
    cash_val = cash[cash["month"] == mth]["cash_usd"].sum()
    text = f"{mth.strftime('%B %Y')} Cash Balance: ${cash_val:,.0f}"
    return "simple_metric", {"value": float(cash_val), "month": mth.isoformat()}, text

def handle_performance_summary(time_info: Dict) -> Tuple[str, Dict, str]:
    """Handle performance summary questions"""
    mth = time_info["specific_month"] or get_latest_month()
    
    # Get key metrics
    rev_budget = metrics.revenue_vs_budget(mth)
    gm_series = metrics.gross_margin_series(1)
    opex_breakdown = metrics.opex_breakdown(mth)
    ebitda_series = metrics.ebitda_series()
    latest_ebitda = ebitda_series[ebitda_series["month"] == mth]["ebitda_usd"].iloc[0] if len(ebitda_series[ebitda_series["month"] == mth]) > 0 else 0
    
    total_opex = opex_breakdown["total_usd"].sum()
    gm_pct = gm_series["gross_margin_pct"].iloc[0] if len(gm_series) > 0 else 0
    
    text = f"""{mth.strftime('%B %Y')} Performance Summary:
- Revenue: ${rev_budget['actual_usd']:,.0f} (vs Budget: ${rev_budget['budget_usd']:,.0f}, {rev_budget['variance_pct']:.1f}%)
- Gross Margin: {gm_pct:.1f}%
- Total Opex: ${total_opex:,.0f}
- EBITDA: ${latest_ebitda:,.0f}"""
    
    return "performance_summary", {
        "revenue": rev_budget,
        "gross_margin_pct": float(gm_pct),
        "total_opex": float(total_opex),
        "ebitda": float(latest_ebitda),
        "month": mth.isoformat()
    }, text

def handle_comparison_query(question: str, time_info: Dict) -> Tuple[str, Dict, str]:
    """Handle comparison questions"""
    # Default to revenue vs budget if not specific
    mth = time_info["specific_month"] or get_latest_month()
    res = metrics.revenue_vs_budget(mth)
    text = f"{mth.strftime('%B %Y')} Revenue vs Budget: Actual ${res['actual_usd']:,.0f}, Budget ${res['budget_usd']:,.0f}, Variance ${res['variance_usd']:,.0f} ({res['variance_pct']:.1f}%)."
    return "revenue_vs_budget", res, text

def handle_growth_query(question: str, time_info: Dict) -> Tuple[str, Dict, str]:
    """Handle growth-related questions"""
    from .data import to_usd
    a, _, fx, _ = load_csvs()
    actuals_usd = to_usd(a, fx)
    
    # Revenue growth by default
    rev_data = actuals_usd[actuals_usd["account_category"] == "Revenue"]
    monthly_rev = rev_data.groupby("month")["amount_usd"].sum().reset_index().sort_values("month")
    
    if len(monthly_rev) >= 2:
        latest = monthly_rev.iloc[-1]
        previous = monthly_rev.iloc[-2]
        growth = ((latest["amount_usd"] - previous["amount_usd"]) / previous["amount_usd"]) * 100
        
        text = f"Revenue Growth: {pd.to_datetime(latest['month']).strftime('%B %Y')} vs {pd.to_datetime(previous['month']).strftime('%B %Y')}: {growth:.1f}% (${latest['amount_usd']:,.0f} vs ${previous['amount_usd']:,.0f})"
        return "growth_analysis", {
            "current": float(latest["amount_usd"]),
            "previous": float(previous["amount_usd"]),
            "growth_pct": float(growth),
            "current_month": latest["month"],
            "previous_month": previous["month"]
        }, text
    
    return "simple_metric", {}, "Insufficient data for growth analysis."

def handle_general_financial_query(question: str, time_info: Dict) -> Tuple[str, Dict, str]:
    """Handle any other financial query by providing a summary"""
    mth = time_info["specific_month"] or get_latest_month()
    
    # Provide a general financial snapshot
    from .data import to_usd
    a, _, fx, cash = load_csvs()
    actuals_usd = to_usd(a, fx)
    
    month_data = actuals_usd[actuals_usd["month"] == mth]
    revenue = month_data[month_data["account_category"] == "Revenue"]["amount_usd"].sum()
    cogs = month_data[month_data["account_category"] == "COGS"]["amount_usd"].sum()
    opex = month_data[month_data["account_category"].str.startswith("Opex:")]["amount_usd"].sum()
    cash_balance = cash[cash["month"] == mth]["cash_usd"].sum()
    
    gross_margin = ((revenue - cogs) / revenue * 100) if revenue > 0 else 0
    ebitda = revenue - cogs - opex
    
    text = f"""{mth.strftime('%B %Y')} Financial Snapshot:
- Revenue: ${revenue:,.0f}
- COGS: ${cogs:,.0f}
- Gross Margin: {gross_margin:.1f}%
- Opex: ${opex:,.0f}
- EBITDA: ${ebitda:,.0f}
- Cash: ${cash_balance:,.0f}"""
    
    return "financial_snapshot", {
        "revenue": float(revenue),
        "cogs": float(cogs),
        "gross_margin_pct": float(gross_margin),
        "opex": float(opex),
        "ebitda": float(ebitda),
        "cash": float(cash_balance),
        "month": mth.isoformat()
    }, text
