import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------- #
# 🚀 PAGE CONFIGURATION
# --------------------------- #
st.set_page_config(page_title="📊 Financial Performance Dashboard", layout="wide")
st.title("📈 Financial Performance Dashboard")

# --------------------------- #
# 📂 FILE UPLOAD SECTION
# --------------------------- #
df = st.file_uploader("📤 Upload your Financial Dataset (.csv or .xlsx)", type=["csv", "xlsx"])

if df:
    # Load data
    data = pd.read_csv(df) if df.name.endswith(".csv") else pd.read_excel(df)

    # --------------------------- #
    # 🧹 CLEAN & RENAME COLUMNS
    # --------------------------- #
    data.columns = data.columns.str.strip()
    column_renames = {
        ' Product ': 'Product',
        ' Discount Band ': 'Discount Band',
        ' Units Sold ': 'Units Sold',
        ' Manufacturing Price ': 'Manufacturing Price',
        ' Sale Price ': 'Sale Price',
        ' Gross Sales ': 'Gross Sales',
        ' Discounts ': 'Discounts',
        '  Sales ': 'Sales',
        ' COGS ': 'COGS',
        ' Profit ': 'Profit',
        ' Month Name ': 'Month Name'
    }
    data.rename(columns=column_renames, inplace=True)

    # --------------------------- #
    # 🔢 CLEAN NUMERIC CURRENCY COLUMNS
    # --------------------------- #
    currency_columns = [
        'Units Sold', 'Manufacturing Price', 'Sale Price',
        'Gross Sales', 'Discounts', 'Sales', 'COGS', 'Profit'
    ]
    for col in currency_columns:
        if col in data.columns:
            data[col] = data[col].replace('[\$,]', '', regex=True).replace('-', '0')
            data[col] = pd.to_numeric(data[col], errors='coerce')

    # --------------------------- #
    # 🗓️ DATE PARSING
    # --------------------------- #
    if 'Date' in data.columns:
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        data['Year'] = data['Date'].dt.year
        data['Month Name'] = data['Date'].dt.month_name()

    # --------------------------- #
    # 🧮 CALCULATED FIELDS
    # --------------------------- #
    if {'Profit', 'Sales'}.issubset(data.columns):
        data['Profit Margin'] = data['Profit'].div(data['Sales'].replace(0, pd.NA))
    if {'COGS', 'Sales'}.issubset(data.columns):
        data['COGS to Sales'] = data['COGS'].div(data['Sales'].replace(0, pd.NA))
    if {'Gross Sales', 'Discounts'}.issubset(data.columns):
        data['Net Sales'] = data['Gross Sales'] - data['Discounts']

    # --------------------------- #
    # 🧰 FILTERS (SIDEBAR)
    # --------------------------- #
    st.sidebar.header("🔍 Filter Data")
    segment_filter = st.sidebar.multiselect(
        "Segment", data['Segment'].dropna().unique() if 'Segment' in data.columns else [], default=None)
    country_filter = st.sidebar.multiselect(
        "Country", data['Country'].dropna().unique() if 'Country' in data.columns else [], default=None)
    year_filter = st.sidebar.multiselect(
        "Year", data['Year'].dropna().unique() if 'Year' in data.columns else [], default=None)

    filtered_data = data.copy()
    if segment_filter and 'Segment' in data.columns:
        filtered_data = filtered_data[filtered_data['Segment'].isin(segment_filter)]
    if country_filter and 'Country' in data.columns:
        filtered_data = filtered_data[filtered_data['Country'].isin(country_filter)]
    if year_filter and 'Year' in data.columns:
        filtered_data = filtered_data[filtered_data['Year'].isin(year_filter)]

    # --------------------------- #
    # 📊 KPI METRICS
    # --------------------------- #
    st.markdown("## 📌 Key Performance Indicators")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Sales", f"${filtered_data['Sales'].sum():,.0f}" if 'Sales' in filtered_data.columns else "N/A")
    kpi2.metric("Total Profit", f"${filtered_data['Profit'].sum():,.0f}" if 'Profit' in filtered_data.columns else "N/A")
    kpi3.metric("Total COGS", f"${filtered_data['COGS'].sum():,.0f}" if 'COGS' in filtered_data.columns else "N/A")
    kpi4.metric("Total Discounts", f"${filtered_data['Discounts'].sum():,.0f}" if 'Discounts' in filtered_data.columns else "N/A")

    st.markdown("---")

    # --------------------------- #
    # 📈 TABS FOR DATA VISUALIZATIONS
    # --------------------------- #
    tab1, tab2, tab3, tab4 = st.tabs(["🌍 Sales by Country", "📆 Trend Over Time", "💸 Gross vs Discount", "🔥 Product Heatmap"])

    with tab1:
        if {'Country', 'Sales', 'Profit'}.issubset(filtered_data.columns):
            country_summary = filtered_data.groupby('Country')[['Sales', 'Profit']].sum().reset_index()
            fig1 = px.bar(country_summary, x='Country', y='Sales', color='Profit', title="Sales and Profit by Country")
            st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        if {'Year', 'Month Name', 'Sales'}.issubset(filtered_data.columns):
            trend_data = filtered_data.groupby(['Year', 'Month Name'])[['Sales', 'Profit']].sum().reset_index()
            fig2 = px.line(trend_data, x='Month Name', y='Sales', color='Year', markers=True, title="Monthly Sales Trends")
            st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        if {'Gross Sales', 'Discounts', 'Country'}.issubset(filtered_data.columns):
            fig3 = px.scatter(filtered_data, x='Gross Sales', y='Discounts', color='Country', title="Gross Sales vs Discounts")
            st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        if {'Product', 'Discount Band', 'Sales'}.issubset(filtered_data.columns):
            heatmap = filtered_data.groupby(['Product', 'Discount Band'])['Sales'].sum().reset_index()
            fig4 = px.density_heatmap(heatmap, x='Discount Band', y='Product', z='Sales',
                                      color_continuous_scale='Viridis', title="Sales by Product and Discount Band")
            st.plotly_chart(fig4, use_container_width=True)

else:
    st.info("📂 Please upload a dataset file to begin analyzing.")

         




