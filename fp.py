import streamlit as st
import pandas as pd
import plotly.express as px

# Title and Sidebar Setup
st.set_page_config(page_title="Financial Performance Dashboard", layout="wide")
st.title("📊 Financial Performance Dashboard")

# Upload Dataset
df = st.file_uploader("Upload Financial Dataset (.csv or .xlsx)", type=["csv", "xlsx"])

if df:
    # Load dataset
    if df.name.endswith(".csv"):
        data = pd.read_csv(df)
    else:
        data = pd.read_excel(df)

    # Clean column names
    data.columns = data.columns.str.strip()

    # Debug: show available columns
    st.write("Available columns:", data.columns.tolist())

    # Convert and extract date components if 'Date' exists
    if 'Date' in data.columns:
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        data['Year'] = pd.DatetimeIndex(data['Date']).year
        data['Month Name'] = pd.DatetimeIndex(data['Date']).month_name()

    # Create calculated fields safely
    if 'Profit' in data.columns and 'Sales' in data.columns:
        data['Profit Margin'] = data['Profit'] / data['Sales']
    if 'Discounts' in data.columns:
        data['Total Discounts'] = data['Discounts']
    if 'Gross Sales' in data.columns:
        data['Total Revenue'] = data['Gross Sales']
    if 'COGS' in data.columns and 'Sales' in data.columns:
        data['COGS to Sales'] = data['COGS'] / data['Sales']
    if 'Gross Sales' in data.columns and 'Discounts' in data.columns:
        data['Net Sales'] = data['Gross Sales'] - data['Discounts']

    # Sidebar Filters with column checks
    st.sidebar.header("Filters")
    segment_options = data['Segment'].unique().tolist() if 'Segment' in data.columns else []
    country_options = data['Country'].unique().tolist() if 'Country' in data.columns else []
    year_options = data['Year'].dropna().unique().tolist() if 'Year' in data.columns else []

    selected_segment = st.sidebar.multiselect("Segment", options=segment_options, default=segment_options)
    selected_country = st.sidebar.multiselect("Country", options=country_options, default=country_options)
    selected_year = st.sidebar.multiselect("Year", options=year_options, default=year_options)

    filtered_data = data.copy()
    if 'Segment' in data.columns:
        filtered_data = filtered_data[filtered_data['Segment'].isin(selected_segment)]
    if 'Country' in data.columns:
        filtered_data = filtered_data[filtered_data['Country'].isin(selected_country)]
    if 'Year' in data.columns:
        filtered_data = filtered_data[filtered_data['Year'].isin(selected_year)]

    # KPI Metrics
    total_sales = filtered_data['Sales'].sum() if 'Sales' in filtered_data.columns else 0
    total_profit = filtered_data['Profit'].sum() if 'Profit' in filtered_data.columns else 0
    total_cogs = filtered_data['COGS'].sum() if 'COGS' in filtered_data.columns else 0
    total_discount = filtered_data['Discounts'].sum() if 'Discounts' in filtered_data.columns else 0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Sales", f"${total_sales:,.0f}")
    kpi2.metric("Total Profit", f"${total_profit:,.0f}")
    kpi3.metric("Total COGS", f"${total_cogs:,.0f}")
    kpi4.metric("Total Discounts", f"${total_discount:,.0f}")

    st.markdown("---")

    # Tabs for visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Sales by Country", "Trend Over Time", "Gross vs Discount", "Product Discounts"])

    with tab1:
        if {'Country', 'Sales', 'Profit'}.issubset(filtered_data.columns):
            chart_data = filtered_data.groupby('Country').agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
            fig = px.bar(chart_data, x='Country', y='Sales', color='Profit', title="Sales and Profit by Country")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        if {'Year', 'Month Name'}.issubset(filtered_data.columns):
            trend_data = filtered_data.groupby(['Year', 'Month Name']).agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
            fig = px.line(trend_data, x='Month Name', y='Sales', color='Year', title="Sales Trend Over Time")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        if {'Gross Sales', 'Discounts', 'Country'}.issubset(filtered_data.columns):
            fig = px.scatter(filtered_data, x='Gross Sales', y='Discounts', color='Country', title="Gross Sales vs Discounts")
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        if {'Product', 'Discount Band', 'Sales'}.issubset(filtered_data.columns):
            heatmap_data = filtered_data.groupby(['Product', 'Discount Band']).agg({'Sales': 'sum'}).reset_index()
            fig = px.density_heatmap(
                heatmap_data,
                x='Discount Band',
                y='Product',
                z='Sales',
                color_continuous_scale='Blues',
                title="Sales by Product and Discount Band"
            )
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Please upload the dataset to get started.")


   


