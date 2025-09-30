#  Mini CFO Copilot

An AI-powered financial assistant that answers ANY finance question directly from structured CSV data. Built with Streamlit, this tool transforms hours of manual financial analysis into instant, board-ready insights.

## ✨ What's New - Enhanced Agent

**The agent now answers ANY financial question, not just 4 predefined ones!**

### 🚀 Key Improvements

- **Universal Question Handling**: Ask any financial question in natural language
- **Intelligent Intent Recognition**: Automatically understands what you're asking for
- **Smart Time Period Extraction**: Handles "last 3 months", "June 2025", "YTD", etc.
- **Comprehensive Visualizations**: Automatic charts for all question types
- **Financial Summaries**: Get complete performance overviews
- **Growth Analysis**: Compare periods and track trends

## 📊 Supported Question Types

### Revenue Questions
- "What was June 2025 revenue vs budget?"
- "Show me revenue trend for last 6 months"
- "What's our latest revenue?"
- "How is revenue growing?"

### Profitability Questions
- "Show gross margin trend"
- "What's our EBITDA for March 2025?"
- "How's our performance this month?"
- "Tell me about our profitability"

### Cost Questions
- "Break down Opex by category for June 2025"
- "What are our COGS for latest month?"
- "Show me total Opex for 2025"

### Cash Questions
- "What is our cash runway?"
- "Show cash balance trend"
- "What's our current cash position?"
- "How much cash do we have?"

### Growth & Comparison
- "Compare this month vs last month"
- "Show me year over year growth"
- "Compare revenue vs budget"

### General Financial Insights
- "Give me a financial summary"
- "How are we performing?"
- "Show me key metrics for latest month"
- "What's the financial overview?"

## 🎯 Core Metrics Calculated

- **Revenue (USD)**: Actual vs budget with variance analysis
- **Gross Margin %**: (Revenue – COGS) / Revenue
- **Opex Total (USD)**: Grouped by categories (Marketing, Sales, R&D, Admin)
- **EBITDA**: Revenue – COGS – Opex (proxy calculation)
- **Cash Runway**: Cash ÷ avg monthly net burn (last 3 months)

## 🏗️ Architecture

```
mini-cfo-copilot/
├── app.py              # Streamlit web interface
├── agent/              # AI agent components
│   ├── planner.py      # Enhanced question understanding & routing
│   ├── metrics.py      # Financial calculations
│   └── data.py         # CSV data loading & processing
├── fixtures/           # Sample financial data
│   ├── actuals.csv     # Monthly actuals by entity/account
│   ├── budget.csv      # Monthly budget by entity/account
│   ├── fx.csv          # Currency exchange rates
│   └── cash.csv        # Monthly cash balances
├── tests/              # Unit tests
└── requirements.txt    # Dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
streamlit run app.py
```

### 3. Ask Questions!
Open your browser to `http://localhost:8501` and start asking financial questions.

## 🧪 Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Test Enhanced Agent
```bash
python test_enhanced_agent.py
```

**Current Test Results**: ✅ 100% success rate (20/20 questions handled)

## 📈 Sample Questions & Results

### Revenue Analysis
**Q**: "What was June 2025 revenue vs budget?"  
**A**: June 2025 Revenue vs Budget: Actual $1,014,896, Budget $1,072,688, Variance $-57,792 (-5.4%).

### Performance Summary
**Q**: "How's our performance this month?"  
**A**: December 2025 Performance Summary:
- Revenue: $1,107,090 (vs Budget: $1,170,157, -5.4%)
- Gross Margin: 84.8%
- Total Opex: $468,127
- EBITDA: $470,329

### Growth Analysis
**Q**: "How is revenue growing?"  
**A**: Revenue Growth: December 2025 vs November 2025: 2.5% ($1,107,090 vs $1,080,090)

## 🎨 Features

### 📊 Interactive Charts
- Revenue vs Budget comparisons
- Trend lines for margins and growth
- Pie charts for expense breakdowns
- Waterfall charts for financial flow

### 📱 Responsive Design
- Clean, professional interface
- Mobile-friendly layout
- Expandable data previews
- Sample question guidance

### 📄 PDF Export
Generate board-ready reports with:
- Latest Revenue vs Budget
- Opex breakdown
- Cash trend analysis

## 🔧 Technical Details

### Enhanced Agent Intelligence
The planner now uses sophisticated pattern matching to:
- Extract time periods from natural language
- Identify financial concepts and metrics
- Route to appropriate calculation functions
- Generate contextual responses with charts

### Data Processing
- Multi-currency support with FX conversion
- Entity-level consolidation
- Account category mapping
- Time series analysis

### Visualization Engine
- Plotly for interactive charts
- Matplotlib for PDF exports
- Streamlit metrics for KPIs
- Responsive chart layouts

## 🎯 Success Metrics

- **Question Coverage**: 100% success rate on diverse financial questions
- **Response Time**: < 2 seconds for most queries
- **Accuracy**: Validated against manual calculations
- **User Experience**: Intuitive natural language interface

## 🚀 Future Enhancements

- [ ] Multi-company comparisons
- [ ] Forecasting and projections
- [ ] Custom KPI definitions
- [ ] Email report scheduling
- [ ] API endpoints for integration

## 📝 License

This project is built for the FP&A Coding Assignment and demonstrates end-to-end agent design with data analysis, intelligent question processing, and user experience.

---

**Built with**: Python, Streamlit, Pandas, Plotly, and intelligent agent design principles.
