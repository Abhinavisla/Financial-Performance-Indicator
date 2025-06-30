import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
# from streamlit_extras.metric_cards import style_metric_cards

st.set_page_config(page_title="📊 Financial Performance Dashboard", layout="wide")
st.markdown("""
    <style>
body, .stApp {
    background-color: white !important;
    color: black !important; /* Changed to black */
}
.big-title {
    font-size: 2.5rem;
    font-weight: 700;
    color: #004080 !important;
}
.sub {
    font-size: 1.2rem;
    color: #555 !important;
}
.stButton>button, .stSelectbox>div>div>div {
    background-color: #004080 !important;
    color: white !important;
    border-radius: 5px;
    border: none;
}
.stDataFrame, .stTable {
    background-color: white !important;
    color: black !important; /* Changed to black for DataFrame/Table text */
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='big-title'>📈 Financial Performance Dashboard</div>", unsafe_allow_html=True)

# Upload file
uploaded_file = st.file_uploader("📤 Upload your Financial Dataset (.csv or .xlsx)", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    df.rename(columns={
        ' Product ': 'Product', ' Discount Band ': 'Discount Band', ' Units Sold ': 'Units Sold',
        ' Manufacturing Price ': 'Manufacturing Price', ' Sale Price ': 'Sale Price',
        ' Gross Sales ': 'Gross Sales', ' Discounts ': 'Discounts', ' Sales ': 'Sales',
        ' COGS ': 'COGS', ' Profit ': 'Profit', ' Month Name ': 'Month Name'
    }, inplace=True)

    for col in ['Units Sold', 'Manufacturing Price', 'Sale Price', 'Gross Sales', 'Discounts', 'Sales', 'COGS', 'Profit']:
        if col in df.columns:
            df[col] = df[col].replace('[\$,]', '', regex=True).replace('-', '0')
            df[col] = pd.to_numeric(df[col], errors='coerce')

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Year'] = df['Date'].dt.year
        df['Month Name'] = df['Date'].dt.month_name()

    df['Profit Margin'] = df['Profit'] / df['Sales'].replace(0, pd.NA)
    df['COGS to Sales'] = df['COGS'] / df['Sales'].replace(0, pd.NA)
    df['Net Sales'] = df['Gross Sales'] - df['Discounts']
    df['Cumulative Sales'] = df['Sales'].cumsum()

    # Sidebar filters
    st.sidebar.header("🧰 Filter Panel")
    filters = {}

    if 'Date' in df.columns:
        df['Quarter'] = df['Date'].dt.to_period('Q').astype(str)
        date_min = df['Date'].min()
        date_max = df['Date'].max()
        filters['Date'] = st.sidebar.date_input("Date Range", [date_min, date_max], min_value=date_min, max_value=date_max)
        filters['Quarter'] = st.sidebar.multiselect("Quarter", df['Quarter'].dropna().unique(), default=list(df['Quarter'].dropna().unique()))
    for col in ['Segment', 'Country', 'Year', 'Product']:
        if col in df.columns:
            filters[col] = st.sidebar.multiselect(f"{col}", df[col].dropna().unique(), default=list(df[col].dropna().unique()))

    filtered_df = df.copy()
    for col, selected in filters.items():
        if col == 'Date' and isinstance(selected, list) and len(selected) == 2:
            start_date = pd.to_datetime(selected[0])
            end_date = pd.to_datetime(selected[1])
            filtered_df = filtered_df[(filtered_df['Date'] >= start_date) & (filtered_df['Date'] <= end_date)]
        else:
            filtered_df = filtered_df[filtered_df[col].isin(selected)]

    # KPI Section
    st.subheader("📌 Overall Financial Summary")
    col1, col2, col3 = st.columns(3)
    total_sales = filtered_df['Sales'].sum()
    total_profit = filtered_df['Profit'].sum()
    total_cogs = filtered_df['COGS'].sum()
    col1.metric("Total Sales", f"${total_sales:,.0f}", help="Sum of all sales")
    col2.metric("Total Profit", f"${total_profit:,.0f}", help="Sum of all profits")
    col3.metric("Total COGS", f"${total_cogs:,.0f}", help="Sum of Cost of Goods Sold")
    # style_metric_cards()

    if 'Year' in filtered_df.columns:
        sales_by_year = filtered_df.groupby('Year')['Sales'].sum().reset_index()
        profit_by_year = filtered_df.groupby('Year')['Profit'].sum().reset_index()
        max_sales_year = sales_by_year.loc[sales_by_year['Sales'].idxmax()]
        max_profit_year = profit_by_year.loc[profit_by_year['Profit'].idxmax()]

        st.markdown(f"""
            <div class='sub'>
            📈 <b>Highest Sales Year:</b> {int(max_sales_year['Year'])} (${max_sales_year['Sales']:,.0f})  
            💰 <b>Highest Profit Year:</b> {int(max_profit_year['Year'])} (${max_profit_year['Profit']:,.0f})
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 Visual Insights")

    with st.expander("📌 View Key Visualizations", expanded=True):
        tabs = st.tabs(["By Segment", "Profitability Heatmap", "Product Treemap", "Discount Impact", "YoY Trend"])

        with tabs[0]:
            if {'Segment', 'Sales'}.issubset(filtered_df.columns):
                seg_data = filtered_df.groupby('Segment')['Sales'].sum().reset_index()
                fig = px.bar(seg_data, x='Segment', y='Sales', color='Segment', title="Sales by Segment", text_auto='.2s')
                st.plotly_chart(fig, use_container_width=True)

        with tabs[1]:
            if {'Country', 'Segment', 'Profit'}.issubset(filtered_df.columns):
                heat = filtered_df.groupby(['Country', 'Segment'])['Profit'].sum().reset_index()
                fig = px.density_heatmap(heat, x='Segment', y='Country', z='Profit', title="Profitability by Country and Segment", color_continuous_scale='Reds')
                st.plotly_chart(fig, use_container_width=True)

        with tabs[2]:
            if {'Product', 'Sales'}.issubset(filtered_df.columns):
                prod = filtered_df.groupby('Product')['Sales'].sum().reset_index()
                fig = px.treemap(prod, path=['Product'], values='Sales', title="Sales Distribution by Product")
                st.plotly_chart(fig, use_container_width=True)

        with tabs[3]:
            if {'Discounts', 'Profit', 'Segment'}.issubset(filtered_df.columns):
                fig = px.scatter(filtered_df, x='Discounts', y='Profit', color='Segment', title="Discount Impact on Profit")
                st.plotly_chart(fig, use_container_width=True)

        with tabs[4]:
            metric = st.selectbox("Select metric for Year-over-Year Analysis", ['Sales', 'Profit', 'COGS'])
            if {'Year', 'Month Name', metric}.issubset(filtered_df.columns):
                trend = filtered_df.groupby(['Year', 'Month Name'])[metric].sum().reset_index()
                fig = px.line(trend, x='Month Name', y=metric, color='Year', markers=True, title=f"Year-over-Year {metric} Trends")
                st.plotly_chart(fig, use_container_width=True)

    # Extra Insights
    st.markdown("---")
    with st.expander("📈 Advanced Metrics"):
        if 'Profit Margin' in filtered_df.columns:
            margin = filtered_df.groupby('Product')['Profit Margin'].mean().reset_index().sort_values(by='Profit Margin', ascending=False)
            fig = px.bar(margin.head(10), x='Profit Margin', y='Product', orientation='h', title="Top 10 Products by Avg. Profit Margin")
            st.plotly_chart(fig, use_container_width=True)

        if 'COGS to Sales' in filtered_df.columns:
            ratio = filtered_df.groupby('Segment')['COGS to Sales'].mean().reset_index()
            fig = px.pie(ratio, names='Segment', values='COGS to Sales', title="Avg. COGS-to-Sales Ratio by Segment")
            st.plotly_chart(fig, use_container_width=True)

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

    st.markdown("### Revenue Growth Strategies")
    st.markdown("""
    - **Identify High-Growth Segments:** Analyze sales by segment to pinpoint areas with the highest growth potential. Allocate more resources to these segments to maximize returns.
    - **Optimize Pricing:** Review `Sale Price` and `Manufacturing Price` to ensure competitive yet profitable pricing strategies. Consider A/B testing different price points.
    - **Expand Product Lines:** Explore opportunities to introduce new products that complement your existing offerings, especially in high-demand areas identified from the `Product Treemap`.
    - **Targeted Marketing Campaigns:** Use insights from `Country` and `Segment` data to tailor marketing efforts, focusing on regions and customer groups with the highest sales potential.
    """)

    st.markdown("### Cost Management and Efficiency")
    st.markdown("""
    - **Control COGS:** Regularly review your `Cost of Goods Sold (COGS)` and `COGS to Sales` ratio. Look for ways to reduce supplier costs, optimize production processes, or improve inventory management.
    - **Minimize Unnecessary Discounts:** While discounts can drive sales, excessive `Discounts` can erode `Profit`. Use the "Discount Impact on Profit" visualization to understand the ideal discount levels for different segments. Implement data-driven discount strategies.
    - **Streamline Operations:** Analyze operational expenses that contribute to COGS. Identify bottlenecks or inefficiencies in your supply chain and manufacturing processes to reduce costs.
    """)

    st.markdown("### Profitability Enhancement")
    st.markdown("""
    - **Boost Profit Margins:** Continuously monitor `Profit Margin` by product. Focus on promoting products with higher profit margins and consider strategies to improve the margins of lower-performing products (e.g., cost reduction, price adjustments).
    - **Strategic Product Mix:** Shift focus towards selling a higher proportion of products with better `Profit Margin` and `Sales` performance.
    - **Analyze Underperforming Areas:** Investigate segments, countries, or products with low `Profit` or negative `Profit Margin`. Develop specific action plans to either improve their profitability or consider phasing them out.
    """)

    st.markdown("### Data-Driven Decision Making")
    st.markdown("""
    - **Leverage Year-over-Year Trends:** Use the "Year-over-Year Trends" analysis to forecast future performance, identify seasonal fluctuations, and prepare for peak and off-peak periods.
    - **Monitor Key Performance Indicators (KPIs):** Regularly track `Total Sales`, `Total Profit`, and `Total COGS` against your business goals. Set clear targets and use the dashboard to monitor progress.
    - **Conduct Regular Financial Reviews:** Schedule periodic reviews of your Profit and Loss Statement and other key metrics to make timely adjustments to your strategies.
    """)


else:
    st.info("📁 Upload a CSV or Excel file to begin.")
