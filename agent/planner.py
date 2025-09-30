import re
import pandas as pd
from typing import Tuple, Dict, Optional, List
from . import metrics
from .data import load_csvs, to_usd

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

def get_available_data_summary() -> Dict[str, any]:
    """Get summary of what data is available"""
    a, b, fx, cash = load_csvs()
    
    return {
        "date_range": {
            "start": a["month"].min(),
            "end": a["month"].max(),
            "months_available": len(a["month"].unique())
        },
        "entities": list(a["entity"].unique()),
        "account_categories": list(a["account_category"].unique()),
        "currencies": list(a["currency"].unique()),
        "has_budget": len(b) > 0,
        "has_cash": len(cash) > 0,
        "latest_month": get_latest_month()
    }

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

def extract_financial_concepts(question: str) -> List[str]:
    """Extract financial concepts from question using comprehensive pattern matching"""
    q = question.lower()
    concepts = []
    
    # Data availability questions
    if any(phrase in q for phrase in ["what data", "which year", "from which year", "to which year", "data available", "available data", "date range", "time period", "what years", "time range"]):
        concepts.append("data_range")
    
    # Revenue related - comprehensive patterns
    if any(word in q for word in ["revenue", "sales", "income", "top line", "turnover", "receipts", "earnings", "money made", "money earned", "total sales"]):
        concepts.append("revenue")
    
    # Cost related - comprehensive patterns  
    if any(word in q for word in ["cogs", "cost of goods", "cost of sales", "direct cost", "product cost", "manufacturing cost"]):
        concepts.append("cost")
    
    # Opex related - comprehensive patterns
    if any(word in q for word in ["opex", "operating expense", "operational expense", "expenses", "overhead", "admin", "marketing", "sales expense", "r&d", "research", "development"]):
        concepts.append("opex")
    
    # Margin related - comprehensive patterns
    if any(word in q for word in ["margin", "gross margin", "profitability", "profit", "markup", "profit margin", "gm"]):
        concepts.append("margin")
    
    # EBITDA related - comprehensive patterns
    if any(word in q for word in ["ebitda", "earnings", "operating profit", "operating income"]):
        concepts.append("ebitda")
    
    # Cash related - comprehensive patterns
    if any(word in q for word in ["cash", "cash flow", "runway", "burn", "liquidity", "money available", "cash balance", "bank balance"]):
        concepts.append("cash")
    
    # Budget related - comprehensive patterns
    if any(word in q for word in ["budget", "vs budget", "variance", "compare", "comparison", "planned", "forecast", "target", "actual vs", "difference"]):
        concepts.append("budget")
    
    # Growth/trend related
    if any(word in q for word in ["growth", "trend", "increase", "decrease", "growing", "declining", "change", "over time", "monthly", "yearly"]):
        concepts.append("trend")
    
    # Performance related
    if any(phrase in q for phrase in ["performance", "how are we", "how is", "doing", "summary", "overview", "snapshot", "status", "health", "business doing", "company doing", "we doing"]):
        concepts.append("performance")
    
    return concepts

def search_data_for_question(question: str) -> Tuple[str, Dict, str]:
    """Search available data to answer any question with intelligent understanding"""
    q = question.lower()
    
    # Check if question is completely unrelated to finance
    finance_keywords = ["revenue", "sales", "income", "cost", "cogs", "expense", "opex", "margin", "profit", "ebitda", "cash", "budget", "money", "financial", "performance", "data", "year", "month", "trend", "growth", "summary", "total", "amount", "balance", "earnings", "admin", "marketing", "r&d", "research", "development", "overhead", "operating", "business", "company", "doing", "how"]
    
    if not any(keyword in q for keyword in finance_keywords):
        # Completely unrelated question - provide data summary
        a, b, fx, cash = load_csvs()
        actuals_usd = to_usd(a, fx)
        return "data_not_available", {}, "I can only answer questions about financial data. Please ask about revenue, costs, expenses, margins, cash, or other financial metrics."
    
    time_info = extract_time_period(question)
    data_summary = get_available_data_summary()
    
    # Load data
    a, b, fx, cash = load_csvs()
    actuals_usd = to_usd(a, fx)
    budget_usd = to_usd(b, fx) if len(b) > 0 else pd.DataFrame()
    
    # Determine time period to analyze
    if time_info["specific_month"]:
        target_month = time_info["specific_month"]
    else:
        target_month = data_summary["latest_month"] if not time_info["year"] else None
    
    # Check if requested data exists
    if target_month and target_month not in actuals_usd["month"].values:
        available_months = sorted(actuals_usd["month"].unique())
        start_year = available_months[0].year
        end_year = available_months[-1].year
        return "data_not_available", {}, f"Data not available for {target_month.strftime('%B %Y')}. Available data: {start_year} to {end_year} ({available_months[0].strftime('%B %Y')} to {available_months[-1].strftime('%B %Y')})"
    
    # Try to extract specific financial concepts
    concepts = extract_financial_concepts(question)
    
    # Build response based on what's requested and available
    if not concepts:
        # Try to infer from question context
        if any(word in q for word in ["how much", "what is", "show me", "tell me", "give me"]):
            # Likely asking for specific data
            if time_info["year"]:
                return handle_year_summary(actuals_usd, budget_usd, cash, time_info["year"], question)
            return build_financial_snapshot(actuals_usd, budget_usd, cash, target_month, time_info)
        else:
            # General question - provide financial snapshot
            if time_info["year"]:
                return handle_year_summary(actuals_usd, budget_usd, cash, time_info["year"], question)
            return build_financial_snapshot(actuals_usd, budget_usd, cash, target_month, time_info)
    
    # Handle specific concepts with priority order
    q = question.lower()
    
    # Check for specific expense categories first (higher priority)
    if "opex" in concepts or "expenses" in concepts:
        if "marketing" in q:
            return handle_specific_expense_category(actuals_usd, "Marketing", target_month, time_info)
        elif "sales" in q and ("expense" in q or "cost" in q or "spending" in q):
            return handle_specific_expense_category(actuals_usd, "Sales", target_month, time_info)
        elif "r&d" in q or "research" in q or "development" in q:
            return handle_specific_expense_category(actuals_usd, "R&D", target_month, time_info)
        elif "admin" in q or "administration" in q:
            return handle_specific_expense_category(actuals_usd, "Admin", target_month, time_info)
        else:
            if time_info["year"]:
                return handle_specific_metric_year(actuals_usd, "Opex", time_info["year"])
            return handle_opex_analysis(actuals_usd, target_month, time_info, question)
    
    # Then handle other concepts
    for concept in concepts:
        if concept == "data_range":
            return handle_data_range_query(actuals_usd, question)
        elif concept in ["revenue", "sales", "income"] and not ("expense" in q or "cost" in q or "spending" in q):
            if time_info["year"]:
                return handle_specific_metric_year(actuals_usd, "Revenue", time_info["year"])
            return handle_revenue_analysis(actuals_usd, budget_usd, target_month, time_info, question)
        elif concept in ["cost", "cogs", "cost of goods"]:
            if time_info["year"]:
                return handle_specific_metric_year(actuals_usd, "COGS", time_info["year"])
            return handle_cost_analysis(actuals_usd, target_month, time_info, question)
        elif concept in ["margin", "gross margin", "profitability"]:
            return handle_margin_analysis(actuals_usd, target_month, time_info, question)
        elif concept in ["ebitda", "earnings"]:
            if time_info["year"]:
                return handle_specific_metric_year(actuals_usd, "EBITDA", time_info["year"])
            return handle_ebitda_analysis(actuals_usd, target_month, time_info, question)
        elif concept in ["cash", "cash flow", "runway"]:
            return handle_cash_analysis(cash, actuals_usd, target_month, time_info, question)
        elif concept in ["budget", "vs budget", "variance"]:
            return handle_budget_analysis(actuals_usd, budget_usd, target_month, time_info, question)
        elif concept == "trend":
            return handle_trend_analysis(actuals_usd, target_month, time_info, question)
        elif concept == "performance":
            return handle_performance_analysis(actuals_usd, budget_usd, cash, target_month, time_info, question)
    
    # Fallback to general analysis
    if time_info["year"]:
        return handle_year_summary(actuals_usd, budget_usd, cash, time_info["year"], question)
    return build_financial_snapshot(actuals_usd, budget_usd, cash, target_month, time_info)

def plan_and_run(question: str) -> Tuple[str, Dict, str]:
    """Main entry point - handles ANY financial question by searching available data"""
    try:
        return search_data_for_question(question)
    except Exception as e:
        return "error", {}, f"Unable to process question: {str(e)}. Please try rephrasing your question."

def build_financial_snapshot(actuals_usd: pd.DataFrame, budget_usd: pd.DataFrame, cash: pd.DataFrame, target_month: pd.Timestamp, time_info: Dict) -> Tuple[str, Dict, str]:
    """Build comprehensive financial snapshot"""
    if target_month is None:
        target_month = get_latest_month()
    
    month_data = actuals_usd[actuals_usd["month"] == target_month]
    if month_data.empty:
        return "data_not_available", {}, f"No data available for {target_month.strftime('%B %Y')}"
    
    revenue = month_data[month_data["account_category"] == "Revenue"]["amount_usd"].sum()
    cogs = month_data[month_data["account_category"] == "COGS"]["amount_usd"].sum()
    opex = month_data[month_data["account_category"].str.startswith("Opex:")]["amount_usd"].sum()
    
    cash_balance = 0
    if len(cash) > 0:
        cash_month = cash[cash["month"] == target_month]
        if not cash_month.empty:
            cash_balance = cash_month["cash_usd"].sum()
    
    gross_margin = ((revenue - cogs) / revenue * 100) if revenue > 0 else 0
    ebitda = revenue - cogs - opex
    
    text = f"""{target_month.strftime('%B %Y')} Financial Snapshot:
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
        "month": target_month.isoformat()
    }, text

def handle_revenue_analysis(actuals_usd: pd.DataFrame, budget_usd: pd.DataFrame, target_month: pd.Timestamp, time_info: Dict, question: str) -> Tuple[str, Dict, str]:
    """Handle revenue-related questions"""
    q = question.lower()
    
    if "budget" in q or "vs" in q or "variance" in q:
        if len(budget_usd) == 0:
            return "data_not_available", {}, "Budget data not available"
        
        if target_month is None:
            target_month = get_latest_month()
            
        res = metrics.revenue_vs_budget(target_month)
        text = f"{target_month.strftime('%B %Y')} Revenue vs Budget: Actual ${res['actual_usd']:,.0f}, Budget ${res['budget_usd']:,.0f}, Variance ${res['variance_usd']:,.0f} ({res['variance_pct']:.1f}%)"
        return "revenue_vs_budget", res, text
    
    elif "trend" in q or "over time" in q or time_info["last_n"]:
        rev_data = actuals_usd[actuals_usd["account_category"] == "Revenue"]
        monthly_rev = rev_data.groupby("month")["amount_usd"].sum().reset_index().sort_values("month")
        
        if time_info["last_n"]:
            monthly_rev = monthly_rev.tail(time_info["last_n"])
        elif time_info["year"]:
            monthly_rev = monthly_rev[monthly_rev["month"].dt.year == time_info["year"]]
        
        if monthly_rev.empty:
            return "data_not_available", {}, "No revenue data available for requested period"
        
        text = f"Revenue trend over {len(monthly_rev)} months"
        return "revenue_trend", {"series": monthly_rev.to_dict(orient="list")}, text
    
    else:
        # Simple revenue query
        if target_month is None:
            target_month = get_latest_month()
            
        month_data = actuals_usd[(actuals_usd["month"] == target_month) & (actuals_usd["account_category"] == "Revenue")]
        if month_data.empty:
            return "data_not_available", {}, f"No revenue data available for {target_month.strftime('%B %Y')}"
        
        revenue = month_data["amount_usd"].sum()
        text = f"{target_month.strftime('%B %Y')} Revenue: ${revenue:,.0f}"
        return "simple_metric", {"value": float(revenue), "month": target_month.isoformat()}, text

def handle_cost_analysis(actuals_usd: pd.DataFrame, target_month: pd.Timestamp, time_info: Dict, question: str) -> Tuple[str, Dict, str]:
    """Handle cost-related questions"""
    if target_month is None:
        target_month = get_latest_month()
    
    month_data = actuals_usd[(actuals_usd["month"] == target_month) & (actuals_usd["account_category"] == "COGS")]
    if month_data.empty:
        return "data_not_available", {}, f"No COGS data available for {target_month.strftime('%B %Y')}"
    
    cogs = month_data["amount_usd"].sum()
    text = f"{target_month.strftime('%B %Y')} COGS: ${cogs:,.0f}"
    return "simple_metric", {"value": float(cogs), "month": target_month.isoformat()}, text

def handle_opex_analysis(actuals_usd: pd.DataFrame, target_month: pd.Timestamp, time_info: Dict, question: str) -> Tuple[str, Dict, str]:
    """Handle opex-related questions"""
    q = question.lower()
    
    if target_month is None:
        target_month = get_latest_month()
    
    if "breakdown" in q or "category" in q or "categories" in q:
        try:
            df = metrics.opex_breakdown(target_month)
            if df.empty:
                return "data_not_available", {}, f"No Opex data available for {target_month.strftime('%B %Y')}"
            
            text = f"Opex breakdown for {target_month.strftime('%B %Y')} by category"
            return "opex_breakdown", {"table": df.to_dict(orient="records"), "month": target_month.isoformat()}, text
        except:
            return "data_not_available", {}, f"Unable to generate Opex breakdown for {target_month.strftime('%B %Y')}"
    
    else:
        month_data = actuals_usd[(actuals_usd["month"] == target_month) & (actuals_usd["account_category"].str.startswith("Opex:"))]
        if month_data.empty:
            return "data_not_available", {}, f"No Opex data available for {target_month.strftime('%B %Y')}"
        
        opex = month_data["amount_usd"].sum()
        text = f"{target_month.strftime('%B %Y')} Total Opex: ${opex:,.0f}"
        return "simple_metric", {"value": float(opex), "month": target_month.isoformat()}, text

def handle_margin_analysis(actuals_usd: pd.DataFrame, target_month: pd.Timestamp, time_info: Dict, question: str) -> Tuple[str, Dict, str]:
    """Handle margin-related questions"""
    q = question.lower()
    
    if "trend" in q or time_info["last_n"]:
        try:
            last_n = time_info["last_n"] or 12
            df = metrics.gross_margin_series(last_n)
            if df.empty:
                return "data_not_available", {}, "No margin data available for trend analysis"
            
            text = f"Gross Margin trend (last {last_n} months)"
            return "gross_margin_trend", {"series": df.to_dict(orient="list")}, text
        except:
            return "data_not_available", {}, "Unable to calculate margin trend"
    
    else:
        if target_month is None:
            target_month = get_latest_month()
        
        month_data = actuals_usd[actuals_usd["month"] == target_month]
        if month_data.empty:
            return "data_not_available", {}, f"No data available for {target_month.strftime('%B %Y')}"
        
        revenue = month_data[month_data["account_category"] == "Revenue"]["amount_usd"].sum()
        cogs = month_data[month_data["account_category"] == "COGS"]["amount_usd"].sum()
        
        if revenue == 0:
            return "data_not_available", {}, f"No revenue data for margin calculation in {target_month.strftime('%B %Y')}"
        
        margin = ((revenue - cogs) / revenue) * 100
        text = f"{target_month.strftime('%B %Y')} Gross Margin: {margin:.1f}%"
        return "simple_metric", {"value": float(margin), "month": target_month.isoformat()}, text

def handle_ebitda_analysis(actuals_usd: pd.DataFrame, target_month: pd.Timestamp, time_info: Dict, question: str) -> Tuple[str, Dict, str]:
    """Handle EBITDA-related questions"""
    q = question.lower()
    
    try:
        ebitda_df = metrics.ebitda_series().sort_values("month")
        if ebitda_df.empty:
            return "data_not_available", {}, "No EBITDA data available"
        
        if "trend" in q or time_info["last_n"]:
            last_n = time_info["last_n"] or 12
            recent = ebitda_df.tail(last_n)
            text = f"EBITDA trend (last {last_n} months)"
            return "ebitda_trend", {"series": recent.to_dict(orient="list")}, text
        
        else:
            if target_month is None:
                target_month = get_latest_month()
            
            month_ebitda = ebitda_df[ebitda_df["month"] == target_month]
            if month_ebitda.empty:
                return "data_not_available", {}, f"No EBITDA data available for {target_month.strftime('%B %Y')}"
            
            ebitda_val = month_ebitda["ebitda_usd"].iloc[0]
            text = f"{target_month.strftime('%B %Y')} EBITDA: ${ebitda_val:,.0f}"
            return "simple_metric", {"value": float(ebitda_val), "month": target_month.isoformat()}, text
    
    except Exception as e:
        return "data_not_available", {}, f"Unable to calculate EBITDA: {str(e)}"

def handle_cash_analysis(cash: pd.DataFrame, actuals_usd: pd.DataFrame, target_month: pd.Timestamp, time_info: Dict, question: str) -> Tuple[str, Dict, str]:
    """Handle cash-related questions"""
    q = question.lower()
    
    if len(cash) == 0:
        return "data_not_available", {}, "Cash data not available"
    
    if "runway" in q:
        try:
            res = metrics.cash_runway_months()
            mth = pd.to_datetime(res["reference_month"])
            months = res["runway_months"]
            text = f"Cash runway as of {mth.strftime('%B %Y')}: ${res['cash_usd']:,.0f} cash; avg burn ${res['avg_monthly_burn_usd']:,.0f}/mo -> runway {months:.1f} months"
            return "cash_runway", res, text
        except Exception as e:
            return "data_not_available", {}, f"Unable to calculate cash runway: {str(e)}"
    
    else:
        if target_month is None:
            target_month = pd.to_datetime(cash["month"].max())
        
        cash_month = cash[cash["month"] == target_month]
        if cash_month.empty:
            return "data_not_available", {}, f"No cash data available for {target_month.strftime('%B %Y')}"
        
        cash_val = cash_month["cash_usd"].sum()
        text = f"{target_month.strftime('%B %Y')} Cash Balance: ${cash_val:,.0f}"
        return "simple_metric", {"value": float(cash_val), "month": target_month.isoformat()}, text

def handle_year_summary(actuals_usd: pd.DataFrame, budget_usd: pd.DataFrame, cash: pd.DataFrame, year: int, question: str) -> Tuple[str, Dict, str]:
    """Handle year-specific queries"""
    year_data = actuals_usd[actuals_usd["month"].dt.year == year]
    if year_data.empty:
        available_years = sorted(actuals_usd["month"].dt.year.unique())
        return "data_not_available", {}, f"No data available for {year}. Available years: {available_years[0]} to {available_years[-1]}"
    
    revenue = year_data[year_data["account_category"] == "Revenue"]["amount_usd"].sum()
    cogs = year_data[year_data["account_category"] == "COGS"]["amount_usd"].sum()
    opex = year_data[year_data["account_category"].str.startswith("Opex:")]["amount_usd"].sum()
    
    gross_margin = ((revenue - cogs) / revenue * 100) if revenue > 0 else 0
    ebitda = revenue - cogs - opex
    
    months_count = len(year_data["month"].unique())
    
    text = f"""{year} Financial Summary ({months_count} months):
- Revenue: ${revenue:,.0f}
- COGS: ${cogs:,.0f}
- Gross Margin: {gross_margin:.1f}%
- Opex: ${opex:,.0f}
- EBITDA: ${ebitda:,.0f}"""
    
    return "financial_snapshot", {
        "revenue": float(revenue),
        "cogs": float(cogs),
        "gross_margin_pct": float(gross_margin),
        "opex": float(opex),
        "ebitda": float(ebitda),
        "cash": 0,
        "month": f"{year}-12-31"
    }, text

def handle_specific_metric_year(actuals_usd: pd.DataFrame, metric: str, year: int) -> Tuple[str, Dict, str]:
    """Handle specific metric queries for a year"""
    year_data = actuals_usd[actuals_usd["month"].dt.year == year]
    if year_data.empty:
        available_years = sorted(actuals_usd["month"].dt.year.unique())
        return "data_not_available", {}, f"No data available for {year}. Available years: {available_years[0]} to {available_years[-1]}"
    
    if metric == "COGS":
        value = year_data[year_data["account_category"] == "COGS"]["amount_usd"].sum()
        text = f"{year} COGS: ${value:,.0f}"
    elif metric == "Revenue":
        value = year_data[year_data["account_category"] == "Revenue"]["amount_usd"].sum()
        text = f"{year} Revenue: ${value:,.0f}"
    elif metric == "Opex":
        value = year_data[year_data["account_category"].str.startswith("Opex:")]["amount_usd"].sum()
        text = f"{year} Total Opex: ${value:,.0f}"
    elif metric == "EBITDA":
        revenue = year_data[year_data["account_category"] == "Revenue"]["amount_usd"].sum()
        cogs = year_data[year_data["account_category"] == "COGS"]["amount_usd"].sum()
        opex = year_data[year_data["account_category"].str.startswith("Opex:")]["amount_usd"].sum()
        value = revenue - cogs - opex
        text = f"{year} EBITDA: ${value:,.0f}"
    
    return "simple_metric", {"value": float(value), "month": f"{year}-12-31"}, text

def handle_specific_expense_category(actuals_usd: pd.DataFrame, category: str, target_month: pd.Timestamp, time_info: Dict) -> Tuple[str, Dict, str]:
    """Handle specific expense category questions"""
    if time_info["specific_month"]:
        target_month = time_info["specific_month"]
        data = actuals_usd[(actuals_usd["month"] == target_month) & (actuals_usd["account_category"] == f"Opex:{category}")]
        if data.empty:
            return "data_not_available", {}, f"No {category} expense data available for {target_month.strftime('%B %Y')}"
        value = data["amount_usd"].sum()
        text = f"{target_month.strftime('%B %Y')} {category} Expenses: ${value:,.0f}"
        return "simple_metric", {"value": float(value), "month": target_month.isoformat()}, text
    elif time_info["year"]:
        year_data = actuals_usd[actuals_usd["month"].dt.year == time_info["year"]]
        data = year_data[year_data["account_category"] == f"Opex:{category}"]
        if data.empty:
            return "data_not_available", {}, f"No {category} expense data available for {time_info['year']}"
        value = data["amount_usd"].sum()
        text = f"{time_info['year']} {category} Expenses: ${value:,.0f}"
        return "simple_metric", {"value": float(value), "month": f"{time_info['year']}-12-31"}, text
    else:
        if target_month is None:
            target_month = get_latest_month()
        data = actuals_usd[(actuals_usd["month"] == target_month) & (actuals_usd["account_category"] == f"Opex:{category}")]
        if data.empty:
            return "data_not_available", {}, f"No {category} expense data available for {target_month.strftime('%B %Y')}"
        value = data["amount_usd"].sum()
        text = f"{target_month.strftime('%B %Y')} {category} Expenses: ${value:,.0f}"
        return "simple_metric", {"value": float(value), "month": target_month.isoformat()}, text

def handle_trend_analysis(actuals_usd: pd.DataFrame, target_month: pd.Timestamp, time_info: Dict, question: str) -> Tuple[str, Dict, str]:
    """Handle trend/growth questions intelligently"""
    q = question.lower()
    
    # Determine what metric to trend
    if any(word in q for word in ["revenue", "sales"]):
        data = actuals_usd[actuals_usd["account_category"] == "Revenue"]
        metric = "Revenue"
        col = "amount_usd"
    elif any(word in q for word in ["cogs", "cost"]):
        data = actuals_usd[actuals_usd["account_category"] == "COGS"]
        metric = "COGS"
        col = "amount_usd"
    elif any(word in q for word in ["opex", "expense"]):
        data = actuals_usd[actuals_usd["account_category"].str.startswith("Opex:")]
        metric = "Opex"
        col = "amount_usd"
    else:
        # Default to revenue
        data = actuals_usd[actuals_usd["account_category"] == "Revenue"]
        metric = "Revenue"
        col = "amount_usd"
    
    monthly_data = data.groupby("month")[col].sum().reset_index().sort_values("month")
    
    if time_info["last_n"]:
        monthly_data = monthly_data.tail(time_info["last_n"])
    elif time_info["year"]:
        monthly_data = monthly_data[monthly_data["month"].dt.year == time_info["year"]]
    
    if len(monthly_data) < 2:
        return "data_not_available", {}, f"Insufficient data for {metric.lower()} trend analysis"
    
    text = f"{metric} trend over {len(monthly_data)} months"
    return "revenue_trend" if metric == "Revenue" else "simple_metric", {"series": monthly_data.to_dict(orient="list")}, text

def handle_performance_analysis(actuals_usd: pd.DataFrame, budget_usd: pd.DataFrame, cash: pd.DataFrame, target_month: pd.Timestamp, time_info: Dict, question: str) -> Tuple[str, Dict, str]:
    """Handle performance/summary questions"""
    if target_month is None:
        target_month = get_latest_month()
    
    if time_info["year"]:
        return handle_year_summary(actuals_usd, budget_usd, cash, time_info["year"], question)
    
    # Monthly performance summary
    month_data = actuals_usd[actuals_usd["month"] == target_month]
    if month_data.empty:
        return "data_not_available", {}, f"No data available for {target_month.strftime('%B %Y')}"
    
    revenue = month_data[month_data["account_category"] == "Revenue"]["amount_usd"].sum()
    cogs = month_data[month_data["account_category"] == "COGS"]["amount_usd"].sum()
    opex = month_data[month_data["account_category"].str.startswith("Opex:")]["amount_usd"].sum()
    
    gross_margin = ((revenue - cogs) / revenue * 100) if revenue > 0 else 0
    ebitda = revenue - cogs - opex
    
    # Try to get budget comparison
    budget_text = ""
    if len(budget_usd) > 0:
        try:
            budget_data = budget_usd[budget_usd["month"] == target_month]
            if not budget_data.empty:
                budget_rev = budget_data[budget_data["account_category"] == "Revenue"]["amount_usd"].sum()
                if budget_rev > 0:
                    variance = ((revenue - budget_rev) / budget_rev * 100)
                    budget_text = f" (vs Budget: {variance:+.1f}%)"
        except:
            pass
    
    text = f"""{target_month.strftime('%B %Y')} Performance:
- Revenue: ${revenue:,.0f}{budget_text}
- Gross Margin: {gross_margin:.1f}%
- Opex: ${opex:,.0f}
- EBITDA: ${ebitda:,.0f}"""
    
    return "financial_snapshot", {
        "revenue": float(revenue),
        "cogs": float(cogs),
        "gross_margin_pct": float(gross_margin),
        "opex": float(opex),
        "ebitda": float(ebitda),
        "cash": 0,
        "month": target_month.isoformat()
    }, text

def handle_data_range_query(actuals_usd: pd.DataFrame, question: str) -> Tuple[str, Dict, str]:
    """Handle questions about available data range"""
    available_months = sorted(actuals_usd["month"].unique())
    start_year = available_months[0].year
    end_year = available_months[-1].year
    start_month = available_months[0].strftime('%B %Y')
    end_month = available_months[-1].strftime('%B %Y')
    total_months = len(available_months)
    
    text = f"Data is available from {start_year} to {end_year} ({start_month} to {end_month}). Total: {total_months} months of data."
    
    return "simple_metric", {
        "start_year": start_year,
        "end_year": end_year,
        "start_month": start_month,
        "end_month": end_month,
        "total_months": total_months
    }, text

def handle_budget_analysis(actuals_usd: pd.DataFrame, budget_usd: pd.DataFrame, target_month: pd.Timestamp, time_info: Dict, question: str) -> Tuple[str, Dict, str]:
    """Handle budget comparison questions"""
    if len(budget_usd) == 0:
        return "data_not_available", {}, "Budget data not available"
    
    if target_month is None:
        target_month = get_latest_month()
    
    try:
        res = metrics.revenue_vs_budget(target_month)
        text = f"{target_month.strftime('%B %Y')} Revenue vs Budget: Actual ${res['actual_usd']:,.0f}, Budget ${res['budget_usd']:,.0f}, Variance ${res['variance_usd']:,.0f} ({res['variance_pct']:.1f}%)"
        return "revenue_vs_budget", res, text
    except Exception as e:
        return "data_not_available", {}, f"Unable to compare with budget for {target_month.strftime('%B %Y')}: {str(e)}"