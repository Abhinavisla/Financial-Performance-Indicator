import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
# from streamlit_extras.metric_cards import style_metric_cards

st.set_page_config(page_title="📊 Financial Performance Dashboard", layout="wide")
st.markdown("""
    <style>
    .big-title { font-size: 2.5rem; font-weight: 700; color: #004080; }
    .sub { font-size: 1.2rem; color: #555; }
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
        ' Gross Sales ': 'Gross Sales', ' Discounts ': 'Discounts', '  Sales ': 'Sales',
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
    for col in ['Segment', 'Country', 'Year', 'Product']:
        if col in df.columns:
            filters[col] = st.sidebar.multiselect(f"{col}", df[col].dropna().unique(), default=list(df[col].dropna().unique()))

    filtered_df = df.copy()
    for col, selected in filters.items():
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

    # Suggestions Section
    st.markdown("---")
    st.subheader("💡 Tips for Improving Financial Performance")
    tips = [
        "✅ Monitor your Profit Margin regularly to ensure you're not just growing revenue but also maintaining profitability.",
        "✅ Focus on high-performing products by analyzing top sales and profit contributors.",
        "✅ Keep COGS under control by negotiating with suppliers or optimizing supply chain processes.",
        "✅ Reduce unnecessary discounts unless they are part of a planned promotional strategy.",
        "✅ Use year-over-year analysis to identify seasonal patterns and make proactive adjustments.",
        "✅ Explore low-performing segments or countries for cost reduction or marketing refocus.",
        "✅ Track cumulative sales against goals to maintain momentum and motivate teams.",
        "✅ Maintain a balance between Gross Sales and Discounts to protect net profitability."
    ]
    for tip in tips:
        st.markdown(f"- {tip}")

else:
    st.info("📁 Upload a CSV or Excel file to begin.")







         




