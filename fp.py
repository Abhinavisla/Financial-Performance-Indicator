import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="📊 Financial Performance Dashboard", layout="wide")

# Custom CSS for styling (including black text for most elements)
st.markdown("""
    <style>
    body, .stApp {
        background-color: white !important;
        color: black !important; /* All main text to black */
    }
    .big-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #004080 !important;
    }
    .sub {
        font-size: 1.2rem;
        color: black !important; /* Subtitle text to black */
    }
    .stButton>button, .stSelectbox>div>div>div {
        background-color: #004080 !important;
        color: white !important;
        border-radius: 5px;
        border: none;
    }
    .stDataFrame, .stTable {
        background-color: white !important;
        color: black !important; /* DataFrame/Table text to black */
    }
    /* Ensure all other text is black */
    p, li, h1, h2, h3, h4, h5, h6, .stMarkdown, .stText {
        color: black !important;
    }

    /* Financial Summary Metric Values to Blue */
    .stMetric > div > div:nth-child(2) > div {
        color: #004080 !important; /* Blue color for metric values */
        font-weight: bold;
    }

    /* Sidebar Background Color to Blue */
    section.main[data-testid="stSidebar"] {
        background-color: #e6f2ff; /* A light blue color */
        color: black; /* Ensure text inside sidebar is readable */
    }

    /* Change sidebar header color to make it visible on blue background */
    [data-testid="stSidebar"] .st-emotion-cache-vk333a { /* This targets the header element within the sidebar */
        color: black !important; /* Or a darker blue if preferred */
    }

    /* Adjust sidebar multiselect background to be visible on blue sidebar */
    .stMultiSelect div[data-baseweb="select"] {
        background-color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='big-title'>📈 Financial Performance Dashboard</div>", unsafe_allow_html=True)

# Upload file
uploaded_file = st.file_uploader("📤 Upload your Financial Dataset (.csv or .xlsx)", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # Rename and clean columns
    df.rename(columns={
        ' Product ': 'Product', ' Discount Band ': 'Discount Band', ' Units Sold ': 'Units Sold',
        ' Manufacturing Price ': 'Manufacturing Price', ' Sale Price ': 'Sale Price',
        ' Gross Sales ': 'Gross Sales', ' Discounts ': 'Discounts', ' Sales ': 'Sales', # Corrected ' Sales '
        ' COGS ': 'COGS', ' Profit ': 'Profit', ' Month Name ': 'Month Name'
    }, inplace=True)

    for col in ['Units Sold', 'Manufacturing Price', 'Sale Price', 'Gross Sales', 'Discounts', 'Sales', 'COGS', 'Profit']:
        if col in df.columns:
            df[col] = df[col].replace('[\\$,]', '', regex=True).replace('-', '0')
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Year'] = df['Date'].dt.year
        df['Month Name'] = df['Date'].dt.month_name()
    else:
        # If 'Date' column is missing, create dummy columns for filters to avoid errors
        df['Year'] = 2023 # Default year
        df['Month Name'] = 'January' # Default month
        st.warning("Date column not found. Date and Quarter filters may not be fully functional.")


    # Calculated metrics
    df['Profit Margin'] = df['Profit'] / df['Sales'].replace(0, pd.NA)
    df['COGS to Sales'] = df['COGS'] / df['Sales'].replace(0, pd.NA)
    df['Net Sales'] = df['Gross Sales'] - df['Discounts']
    df['Cumulative Sales'] = df['Sales'].cumsum()

    # Sidebar Filters
    st.sidebar.header("🧰 Filter Panel")
    filters = {}

    if 'Date' in df.columns:
        df['Quarter'] = df['Date'].dt.to_period('Q').astype(str)
        date_min = df['Date'].min()
        date_max = df['Date'].max()
        
        # Date Range Filter
        selected_dates = st.sidebar.date_input("Date Range", [date_min, date_max], 
                                               min_value=date_min, max_value=date_max)
        if len(selected_dates) == 2:
            start_date = pd.to_datetime(selected_dates[0])
            end_date = pd.to_datetime(selected_dates[1])
            df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

        # Quarter Filter (only show if 'Quarter' column was successfully created)
        if 'Quarter' in df.columns and not df['Quarter'].empty:
            filters['Quarter'] = st.sidebar.multiselect("Quarter", df['Quarter'].dropna().unique(), 
                                                        default=list(df['Quarter'].dropna().unique()))
        else:
            st.sidebar.info("Quarter filter not available without valid 'Date' column.")
    else:
        st.sidebar.info("Date filters not available without 'Date' column in data.")


    for col in ['Segment', 'Country', 'Year', 'Product']:
        if col in df.columns:
            # Only show unique values that are still present after date filtering
            unique_values = df[col].dropna().unique()
            if unique_values.size > 0:
                filters[col] = st.sidebar.multiselect(f"{col}", unique_values, default=list(unique_values))
            else:
                st.sidebar.warning(f"No data available for {col} after date filtering.")


    filtered_df = df.copy()
    for col, selected in filters.items():
        if col in filtered_df.columns: # Check if column exists in filtered_df after date filter
            filtered_df = filtered_df[filtered_df[col].isin(selected)]
        else:
            st.warning(f"Column '{col}' not found in the filtered data for applying filter.")

    # Check if filtered_df is empty
    if filtered_df.empty:
        st.warning("No data available for the selected filters. Please adjust your filter selections.")
    else:
        # KPIs
        st.subheader("📌 Overall Financial Summary")
        col1, col2, col3 = st.columns(3)
        total_sales = filtered_df['Sales'].sum()
        total_profit = filtered_df['Profit'].sum()
        total_cogs = filtered_df['COGS'].sum()
        col1.metric("Total Sales", f"${total_sales:,.0f}")
        col2.metric("Total Profit", f"${total_profit:,.0f}")
        col3.metric("Total COGS", f"${total_cogs:,.0f}")
        # style_metric_cards() # Disabled to avoid error

        # Year Highlights
        if 'Year' in filtered_df.columns and not filtered_df['Year'].empty:
            sales_by_year = filtered_df.groupby('Year')['Sales'].sum().reset_index()
            profit_by_year = filtered_df.groupby('Year')['Profit'].sum().reset_index()
            
            if not sales_by_year.empty:
                max_sales_year = sales_by_year.loc[sales_by_year['Sales'].idxmax()]
                st.markdown(f"""
                    <div class='sub'>
                    📈 <b>Highest Sales Year:</b> {int(max_sales_year['Year'])} (${max_sales_year['Sales']:,.0f})
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No sales data for year highlights with current filters.")

            if not profit_by_year.empty:
                max_profit_year = profit_by_year.loc[profit_by_year['Profit'].idxmax()]
                st.markdown(f"""
                    <div class='sub'>
                    💰 <b>Highest Profit Year:</b> {int(max_profit_year['Year'])} (${max_profit_year['Profit']:,.0f})
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No profit data for year highlights with current filters.")
        else:
            st.info("Year-based highlights not available without 'Year' column or data.")


        st.markdown("---")
        st.subheader("📊 Visual Insights")

        with st.expander("📌 View Key Visualizations", expanded=True):
            tabs = st.tabs(["By Segment", "Profitability Heatmap", "Product Treemap", "Discount Impact", "YoY Trend"])

            with tabs[0]:
                if {'Segment', 'Sales'}.issubset(filtered_df.columns) and not filtered_df['Segment'].empty:
                    seg_data = filtered_df.groupby('Segment')['Sales'].sum().reset_index()
                    if not seg_data.empty:
                        fig = px.bar(seg_data, x='Segment', y='Sales', color='Segment', title="Sales by Segment", text_auto='.2s')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No sales data by Segment for the selected filters.")
                else:
                    st.info("Please ensure 'Segment' and 'Sales' columns exist and have data.")

            with tabs[1]:
                if {'Country', 'Segment', 'Profit'}.issubset(filtered_df.columns) and not filtered_df[['Country', 'Segment']].empty:
                    heat = filtered_df.groupby(['Country', 'Segment'])['Profit'].sum().reset_index()
                    if not heat.empty:
                        fig = px.density_heatmap(heat, x='Segment', y='Country', z='Profit',
                                                 title="Profitability by Country and Segment", color_continuous_scale='Reds')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No profitability data by Country and Segment for the selected filters.")
                else:
                    st.info("Please ensure 'Country', 'Segment', and 'Profit' columns exist and have data.")

            with tabs[2]:
                if {'Product', 'Sales'}.issubset(filtered_df.columns) and not filtered_df['Product'].empty:
                    prod = filtered_df.groupby('Product')['Sales'].sum().reset_index()
                    if not prod.empty:
                        fig = px.treemap(prod, path=['Product'], values='Sales', title="Sales Distribution by Product")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No sales distribution data by Product for the selected filters.")
                else:
                    st.info("Please ensure 'Product' and 'Sales' columns exist and have data.")

            with tabs[3]:
                if {'Discounts', 'Profit', 'Segment'}.issubset(filtered_df.columns) and not filtered_df[['Discounts', 'Profit']].empty:
                    if not filtered_df.empty:
                        fig = px.scatter(filtered_df, x='Discounts', y='Profit', color='Segment', title="Discount Impact on Profit")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No discount impact data for the selected filters.")
                else:
                    st.info("Please ensure 'Discounts', 'Profit', and 'Segment' columns exist and have data.")

            with tabs[4]:
                metric = st.selectbox("Select metric for Year-over-Year Analysis", ['Sales', 'Profit', 'COGS'])
                if {'Year', 'Month Name', metric}.issubset(filtered_df.columns) and not filtered_df[['Year', 'Month Name']].empty:
                    trend = filtered_df.groupby(['Year', 'Month Name'])[metric].sum().reset_index()
                    if not trend.empty:
                        fig = px.line(trend, x='Month Name', y=metric, color='Year', markers=True,
                                      title=f"Year-over-Year {metric} Trends")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"No Year-over-Year {metric} data for the selected filters.")
                else:
                    st.info(f"Please ensure 'Year', 'Month Name', and '{metric}' columns exist and have data.")

        # Advanced Metrics Section
        st.markdown("---")
        with st.expander("📈 Advanced Metrics"):
            if 'Profit Margin' in filtered_df.columns and not filtered_df['Profit Margin'].empty:
                margin = filtered_df.groupby('Product')['Profit Margin'].mean().reset_index().sort_values(by='Profit Margin', ascending=False)
                if not margin.empty:
                    fig = px.bar(margin.head(10), x='Profit Margin', y='Product', orientation='h', title="Top 10 Products by Avg. Profit Margin")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No Profit Margin data for the selected filters.")
            else:
                st.info("Please ensure 'Profit Margin' and 'Product' columns exist and have data.")

            if 'COGS to Sales' in filtered_df.columns and not filtered_df['COGS to Sales'].empty:
                ratio = filtered_df.groupby('Segment')['COGS to Sales'].mean().reset_index()
                if not ratio.empty:
                    fig = px.pie(ratio, names='Segment', values='COGS to Sales', title="Avg. COGS-to-Sales Ratio by Segment")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No COGS to Sales ratio data for the selected filters.")
            else:
                st.info("Please ensure 'COGS to Sales' and 'Segment' columns exist and have data.")

        # Profit and Loss Statement Section
        st.markdown("---")
        st.subheader("📋 Profit and Loss Statement")

        pnl_data = {
            "Total Revenue (Gross Sales)": filtered_df['Gross Sales'].sum() if 'Gross Sales' in filtered_df.columns else 0,
            "Discounts": filtered_df['Discounts'].sum() if 'Discounts' in filtered_df.columns else 0,
            "Net Sales": filtered_df['Net Sales'].sum() if 'Net Sales' in filtered_df.columns else 0,
            "Cost of Goods Sold (COGS)": filtered_df['COGS'].sum() if 'COGS' in filtered_df.columns else 0,
            "Gross Profit": filtered_df['Sales'].sum() - filtered_df['COGS'].sum() if {'Sales', 'COGS'}.issubset(filtered_df.columns) else 0,
            "Operating Profit (EBIT)": filtered_df['Profit'].sum() if 'Profit' in filtered_df.columns else 0
        }

        pnl_df = pd.DataFrame(list(pnl_data.items()), columns=["Line Item", "Amount ($)"])
        st.dataframe(pnl_df.style.format({"Amount ($)": "${:,.0f}"}), use_container_width=True)

        # Suggestions Section
        st.markdown("---")
        st.subheader("💡 Tips for Improving Financial Performance")

        st.markdown("### 💰 Revenue Enhancement Strategies")
        st.markdown("""
        - **Market Diversification:** Explore new geographic markets or customer segments (e.g., from `Country` and `Segment` analysis) to reduce reliance on single revenue streams.
        - **Upselling & Cross-selling:** Identify opportunities to increase average transaction value by promoting higher-priced products or complementary items.
        - **Product Innovation:** Invest in R&D to develop new products or improve existing ones, catering to evolving customer needs and market trends.
        - **Sales Channel Optimization:** Evaluate the effectiveness of different sales channels (e.g., online, retail, direct sales) and optimize investment in the most profitable ones.
        """)

        st.markdown("### 📉 Cost Reduction & Efficiency")
        st.markdown("""
        - **Supplier Negotiations:** Regularly review contracts with suppliers to secure better pricing or terms for raw materials and services (impacts `Manufacturing Price` and `COGS`).
        - **Operational Automation:** Implement technology and automation to streamline processes, reduce manual labor costs, and improve efficiency.
        - **Inventory Management:** Optimize inventory levels to minimize carrying costs and reduce the risk of obsolescence, which impacts `COGS`.
        - **Energy Efficiency:** Invest in energy-efficient equipment or practices to lower utility expenses.
        """)

        st.markdown("### 📈 Profitability & Margin Optimization")
        st.markdown("""
        - **Value-Based Pricing:** Instead of cost-plus pricing, consider pricing products based on the perceived value to the customer, potentially increasing `Sale Price` and `Profit Margin`.
        - **Discount Strategy Review:** Continuously evaluate the effectiveness of `Discounts`. Are they generating incremental profit or just eroding margins? Focus on targeted promotions.
        - **Product Portfolio Management:** Ruthlessly analyze products based on their `Profit Margin` and `Sales` volume. Consider discontinuing unprofitable products or re-engineering them for better margins.
        - **Cost-Benefit Analysis of New Initiatives:** Before launching new projects, conduct thorough cost-benefit analyses to ensure they contribute positively to the bottom line.
        """)

        st.markdown("### 📊 Financial Health & Stability")
        st.markdown("""
        - **Cash Flow Management:** Maintain healthy cash reserves and manage accounts receivable and payable efficiently to ensure liquidity.
        - **Debt Management:** Minimize high-interest debt and strategically use financing to support growth without burdening profitability.
        - **Regular Financial Audits:** Conduct internal and external audits to ensure accuracy, compliance, and identify areas for financial improvement.
        - **Scenario Planning:** Develop financial models to simulate various economic conditions and prepare contingency plans to mitigate risks.
        """)

        # Rules for Better Financial Performance Section
        st.markdown("---")
        st.subheader("⚖️ Rules for Better Financial Performance")
        st.markdown("""
        These fundamental principles guide sound financial management:

        1.  **Revenue Maximization:** Focus on increasing top-line revenue through strategic sales, marketing, and product development efforts, while maintaining pricing integrity.
        2.  **Cost Control:** Continuously monitor and manage expenses across all departments. Distinguish between necessary costs and discretionary spending, and seek efficiencies.
        3.  **Profitability Focus:** Prioritize `Profit` over mere `Sales` volume. Ensure that every sale contributes positively to the bottom line after accounting for all associated costs.
        4.  **Cash Flow is King:** Understand that cash is the lifeblood of the business. Manage inflows and outflows meticulously to avoid liquidity issues, even if the business is profitable on paper.
        5.  **Effective Resource Allocation:** Allocate capital and human resources to initiatives and areas that offer the highest potential return on investment (`ROI`).
        6.  **Risk Management:** Identify, assess, and mitigate financial risks (e.g., market volatility, credit risk, operational risk) to protect assets and ensure continuity.
        7.  **Financial Planning & Budgeting:** Develop realistic financial plans and budgets, and regularly compare actual performance against these targets to identify deviations and take corrective action.
        8.  **Long-Term Perspective:** Balance short-term financial goals with long-term strategic objectives. Sustainable growth often requires investments that may not yield immediate returns.
        9.  **Data-Driven Decisions:** Base financial decisions on accurate, timely, and insightful data analysis, rather than assumptions or intuition alone.
        10. **Compliance & Ethics:** Adhere to all financial regulations, reporting standards, and ethical practices to maintain trust and avoid legal penalties.
        """)

else:
    st.info("📁 Upload a CSV or Excel file to begin.")
