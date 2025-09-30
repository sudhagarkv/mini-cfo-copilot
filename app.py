import streamlit as st
import pandas as pd
import plotly.express as px
from agent.planner import plan_and_run
from agent import metrics as m

st.set_page_config(
    page_title="Mini CFO Copilot", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Header with better styling
st.markdown("""
<div style="text-align: center; padding: 1rem 0;">
    <h1 style="color: #1f77b4; margin-bottom: 0;">🧮 Mini CFO Copilot</h1>
    <p style="font-size: 1.2em; color: #666; margin-top: 0.5rem;">Ask ANY finance question • Get instant insights with charts</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# Data preview section
with st.expander("📁 Data Preview - View source data", expanded=False):
    from agent.data import load_csvs
    a, b, fx, cash = load_csvs()
    
    tab1, tab2, tab3, tab4 = st.tabs(["Actuals", "Budget", "FX Rates", "Cash"])
    
    with tab1:
        st.markdown("**Monthly Actuals by Entity/Account**")
        st.dataframe(a.head(10), use_container_width=True)
        st.caption(f"Total records: {len(a):,}")
    
    with tab2:
        st.markdown("**Monthly Budget by Entity/Account**")
        st.dataframe(b.head(10), use_container_width=True)
        st.caption(f"Total records: {len(b):,}")
    
    with tab3:
        st.markdown("**Currency Exchange Rates**")
        st.dataframe(fx.head(10), use_container_width=True)
        st.caption(f"Total records: {len(fx):,}")
    
    with tab4:
        st.markdown("**Monthly Cash Balances**")
        st.dataframe(cash.head(10), use_container_width=True)
        st.caption(f"Total records: {len(cash):,}")

# Sample questions in a more organized layout
col1, col2 = st.columns([2, 1])

with col1:
    with st.expander("💡 Sample Questions - Click to see examples", expanded=False):
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Revenue", "💰 Profitability", "💸 Costs", "🔍 Analysis"])
        
        with tab1:
            st.markdown("""
            - What was June 2025 revenue vs budget?
            - Show me revenue trend for last 6 months
            - What's our latest revenue?
            """)
        
        with tab2:
            st.markdown("""
            - Show gross margin trend
            - What's our EBITDA for March 2025?
            - How's our performance this month?
            """)
        
        with tab3:
            st.markdown("""
            - Break down Opex by category for June 2025
            - What are our COGS for latest month?
            - Show me total Opex for 2025
            """)
        
        with tab4:
            st.markdown("""
            - How is revenue growing?
            - Give me a financial summary
            - What is our cash runway?
            """)

with col2:
    st.info("💬 **Try asking in natural language!**\n\nThe AI understands context and time periods like 'last 3 months', 'June 2025', etc.")

# Question input with better styling
st.markdown("### 💬 Ask Your Question")
q = st.text_input(
    "Type your financial question here:", 
    value="What was June 2025 revenue vs budget in USD?",
    placeholder="e.g., Show me revenue trend for last 6 months",
    label_visibility="collapsed"
)

summary_for_pdf = "Snapshot: latest Revenue vs Budget, Opex breakdown, and Cash trend."

if q:
    # Process the question
    with st.spinner("Analyzing your question..."):
        intent, payload, text = plan_and_run(q)
    
    # Display answer with better formatting
    st.markdown("---")
    st.markdown("### 📊 Answer")
    
    # Format the answer text better
    if "\n" in text:
        # Multi-line answers (like summaries)
        st.markdown(f"**{text.split(':')[0]}:**" if ":" in text else "**Result:**")
        formatted_text = text.replace("\n", "\n\n")
        st.markdown(formatted_text)
    else:
        # Single line answers
        st.success(text)
    
    summary_for_pdf = text

    # Revenue vs Budget
    if intent == "revenue_vs_budget":
        st.markdown("#### 📈 Visualization")
        month = pd.to_datetime(payload["month"])
        df = pd.DataFrame([
            {"type": "Actual", "value": payload["actual_usd"]},
            {"type": "Budget", "value": payload["budget_usd"]},
        ])
        fig = px.bar(df, x="type", y="value", text_auto=".2s",
                     title=f"Revenue vs Budget — {month.strftime('%B %Y')} (USD)",
                     color="type", color_discrete_map={"Actual": "#1f77b4", "Budget": "#ff7f0e"})
        fig.update_layout(yaxis_title="USD", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Gross Margin Trend
    elif intent == "gross_margin_trend":
        st.markdown("#### 📈 Visualization")
        series = pd.DataFrame(payload["series"])
        fig = px.line(series, x="month", y="gross_margin_pct", markers=True,
                      title="Gross Margin % Trend", line_shape="spline")
        fig.update_layout(yaxis_title="%", xaxis_title="Month")
        fig.update_traces(line_color="#2ca02c", marker_color="#2ca02c")
        st.plotly_chart(fig, use_container_width=True)

    # Opex Breakdown
    elif intent == "opex_breakdown":
        st.markdown("#### 📈 Visualization")
        table = pd.DataFrame(payload["table"])
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("**Breakdown Table:**")
            st.dataframe(table, use_container_width=True)
        
        with col2:
            fig = px.pie(table, names="category", values="total_usd",
                         title="Opex Breakdown (USD)")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

    # Cash Runway
    elif intent == "cash_runway":
        st.markdown("#### 📈 Visualization")
        e = m.ebitda_series().sort_values("month").tail(12)
        from agent.data import load_csvs
        _, _, _, cash = load_csvs()
        cash12 = (cash.sort_values("month").tail(12)
                       .groupby("month")["cash_usd"].sum().reset_index())
        
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.line(cash12, x="month", y="cash_usd", markers=True,
                           title="Cash Balance (last 12 months)")
            fig1.update_traces(line_color="#17becf", marker_color="#17becf")
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.bar(e.tail(12), x="month", y="ebitda_usd",
                          title="EBITDA Trend")
            fig2.update_traces(marker_color="#ff7f0e")
            st.plotly_chart(fig2, use_container_width=True)

    # Revenue Trend
    elif intent == "revenue_trend":
        st.markdown("#### 📈 Visualization")
        series = pd.DataFrame(payload["series"])
        fig = px.line(series, x="month", y="amount_usd", markers=True,
                      title="Revenue Trend (USD)", line_shape="spline")
        fig.update_layout(yaxis_title="USD", xaxis_title="Month")
        fig.update_traces(line_color="#1f77b4", marker_color="#1f77b4")
        st.plotly_chart(fig, use_container_width=True)

    # EBITDA Trend
    elif intent == "ebitda_trend":
        st.markdown("#### 📈 Visualization")
        series = pd.DataFrame(payload["series"])
        fig = px.line(series, x="month", y="ebitda_usd", markers=True,
                      title="EBITDA Trend (USD)", line_shape="spline")
        fig.update_layout(yaxis_title="USD", xaxis_title="Month")
        fig.update_traces(line_color="#d62728", marker_color="#d62728")
        st.plotly_chart(fig, use_container_width=True)

    # Simple Metric (single value)
    elif intent == "simple_metric":
        if "value" in payload and "month" in payload:
            st.markdown("#### 📊 Metric")
            month = pd.to_datetime(payload["month"])
            value = payload["value"]
            
            # Display as a metric card
            st.metric(
                label=f"{month.strftime('%B %Y')}",
                value=f"${value:,.0f}"
            )

    # Performance Summary
    elif intent == "performance_summary":
        st.markdown("#### 📊 Key Metrics")
        
        # Key metrics display
        col1, col2, col3, col4 = st.columns(4)
        rev_data = payload["revenue"]
        
        with col1:
            st.metric(
                "Revenue", 
                f"${rev_data['actual_usd']:,.0f}",
                delta=f"{rev_data['variance_pct']:.1f}% vs Budget"
            )
        with col2:
            st.metric("Gross Margin", f"{payload['gross_margin_pct']:.1f}%")
        with col3:
            st.metric("Total Opex", f"${payload['total_opex']:,.0f}")
        with col4:
            st.metric("EBITDA", f"${payload['ebitda']:,.0f}")
        
        st.markdown("#### 📈 Revenue vs Budget")
        # Revenue vs Budget chart
        df = pd.DataFrame([
            {"type": "Actual", "value": rev_data["actual_usd"]},
            {"type": "Budget", "value": rev_data["budget_usd"]},
        ])
        fig1 = px.bar(df, x="type", y="value", text_auto=".2s",
                      title="Revenue vs Budget (USD)",
                      color="type", color_discrete_map={"Actual": "#1f77b4", "Budget": "#ff7f0e"})
        fig1.update_layout(yaxis_title="USD", showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    # Growth Analysis
    elif intent == "growth_analysis":
        st.markdown("#### 📈 Growth Analysis")
        current = payload["current"]
        previous = payload["previous"]
        growth_pct = payload["growth_pct"]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric(
                "Growth Rate", 
                f"{growth_pct:.1f}%", 
                delta=f"${current - previous:,.0f}"
            )
        
        with col2:
            df = pd.DataFrame([
                {"Period": "Previous", "Value": previous},
                {"Period": "Current", "Value": current},
            ])
            fig = px.bar(df, x="Period", y="Value", text_auto=".2s",
                         title=f"Growth: {growth_pct:.1f}%",
                         color="Period", color_discrete_map={"Previous": "#ff7f0e", "Current": "#2ca02c"})
            fig.update_layout(yaxis_title="USD", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    # Financial Snapshot
    elif intent == "financial_snapshot":
        st.markdown("#### 📊 Financial Snapshot")
        
        # Key metrics in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Revenue", f"${payload['revenue']:,.0f}")
            st.metric("COGS", f"${payload['cogs']:,.0f}")
        with col2:
            st.metric("Gross Margin", f"{payload['gross_margin_pct']:.1f}%")
            st.metric("Opex", f"${payload['opex']:,.0f}")
        with col3:
            st.metric("EBITDA", f"${payload['ebitda']:,.0f}")
            st.metric("Cash", f"${payload['cash']:,.0f}")
        
        st.markdown("#### 📈 Financial Flow")
        # Waterfall-style chart
        categories = ['Revenue', 'COGS', 'Opex', 'EBITDA']
        values = [payload['revenue'], -payload['cogs'], -payload['opex'], payload['ebitda']]
        colors = ['#2ca02c', '#d62728', '#ff7f0e', '#1f77b4']
        
        fig = px.bar(x=categories, y=values, color=categories,
                     title="Financial Waterfall",
                     color_discrete_sequence=colors)
        fig.update_layout(yaxis_title="USD", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

# Footer section
st.markdown("### 📄 Export Options")
st.info("Generate a board-ready PDF report with key financial metrics and charts.")

if st.button("📄 Export PDF Report", type="secondary", use_container_width=True):
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas
    import matplotlib.pyplot as plt

    from agent.data import load_csvs
    a, _, _, cash = load_csvs()
    latest = pd.to_datetime(a["month"].max())

    # Revenue vs Budget (matplotlib)
    rvb = m.revenue_vs_budget(latest)
    df_rb = pd.DataFrame({"Type":["Actual","Budget"],
                          "USD":[rvb["actual_usd"], rvb["budget_usd"]]})
    plt.figure(); plt.bar(df_rb["Type"], df_rb["USD"])
    plt.title(f"Revenue vs Budget — {latest.strftime('%B %Y')}")
    plt.ylabel("USD")
    tmp1 = "rev_vs_budget.png"; plt.savefig(tmp1, bbox_inches="tight"); plt.close()

    # Opex breakdown
    odf = m.opex_breakdown(latest)
    plt.figure(); plt.pie(odf["total_usd"], labels=odf["category"], autopct="%1.0f%%")
    plt.title(f"Opex Breakdown — {latest.strftime('%B %Y')}")
    tmp2 = "opex.png"; plt.savefig(tmp2, bbox_inches="tight"); plt.close()

    # Cash trend (last 12)
    cash12 = (cash.sort_values("month").tail(12)
                   .groupby("month")["cash_usd"].sum().reset_index())
    plt.figure(); plt.plot(cash12["month"], cash12["cash_usd"], marker="o")
    plt.title("Cash Balance — last 12 months"); plt.ylabel("USD")
    plt.xticks(rotation=45, ha="right")
    tmp3 = "cash.png"; plt.savefig(tmp3, bbox_inches="tight"); plt.close()

    out_path = "cfo_report.pdf"
    c = canvas.Canvas(out_path, pagesize=LETTER)
    width, height = LETTER
    y = height - 72
    c.setFont("Helvetica-Bold", 16); c.drawString(72, y, "Mini CFO Copilot — Snapshot"); y -= 20
    c.setFont("Helvetica", 10); c.drawString(72, y, summary_for_pdf[:120]); y -= 30
    for img in [tmp1, tmp2, tmp3]:
        c.drawImage(img, 72, y-250, width=468, height=250, preserveAspectRatio=True)
        y -= 270
        if y < 150:
            c.showPage()
            y = height - 72
    c.save()
    st.success("✅ PDF report generated successfully!")

    with open(out_path, "rb") as f:
        st.download_button(
            "📄 Download PDF Report", 
            data=f, 
            file_name="cfo_report.pdf", 
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
