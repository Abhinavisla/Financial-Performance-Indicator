import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="📊 Financial Performance Dashboard", layout="wide")
st.title("📈 Financial Performance Dashboard")

# Upload file
uploaded_file = st.file_uploader("📤 Upload your Financial Dataset (.csv or .xlsx)", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # Rename and clean up columns
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

    # Filters
    st.sidebar.header("🔍 Filter Panel")
    filters = {}
    for col in ['Segment', 'Country', 'Year', 'Product']:
        if col in df.columns:
            filters[col] = st.sidebar.multiselect(f"{col}", df[col].dropna().unique(), default=list(df[col].dropna().unique()))
    filtered_df = df.copy()
    for col, selected in filters.items():
        filtered_df = filtered_df[filtered_df[col].isin(selected)]

    # KPIs
    st.subheader("📌 Overall Summary")
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Sales", f"${filtered_df['Sales'].sum():,.0f}")
    k2.metric("Total Profit", f"${filtered_df['Profit'].sum():,.0f}")
    k3.metric("Total COGS", f"${filtered_df['COGS'].sum():,.0f}")

    st.markdown("---")
    st.subheader("📊 Dashboard Overview")

    # Layout: 2 columns with 3 charts
    col1, col2 = st.columns(2)

    with col1:
        if {'Segment', 'Sales'}.issubset(filtered_df.columns):
            st.plotly_chart(px.bar(filtered_df.groupby('Segment')['Sales'].sum().reset_index(), x='Segment', y='Sales', title="Sales by Segment"), use_container_width=True)
        if {'Country', 'Segment', 'Profit'}.issubset(filtered_df.columns):
            heat = filtered_df.groupby(['Country', 'Segment'])['Profit'].sum().reset_index()
            st.plotly_chart(px.density_heatmap(heat, x='Segment', y='Country', z='Profit', title="Profitability by Country and Segment", color_continuous_scale='Reds'), use_container_width=True)

    with col2:
        if {'Product', 'Sales'}.issubset(filtered_df.columns):
            prod = filtered_df.groupby('Product')['Sales'].sum().reset_index()
            st.plotly_chart(px.treemap(prod, path=['Product'], values='Sales', title="Sales by Product"), use_container_width=True)
        if {'Discounts', 'Profit'}.issubset(filtered_df.columns):
            st.plotly_chart(px.scatter(filtered_df, x='Discounts', y='Profit', color='Segment', title="Discount Impact on Profit"), use_container_width=True)

    # Year-over-Year trend with parameter control
    metric = st.selectbox("Select metric to analyze YoY trends", ['Sales', 'Profit', 'COGS'])
    if {'Year', 'Month Name', metric}.issubset(filtered_df.columns):
        trend = filtered_df.groupby(['Year', 'Month Name'])[metric].sum().reset_index()
        st.plotly_chart(px.line(trend, x='Month Name', y=metric, color='Year', markers=True, title=f"Year-over-Year {metric} Trends"), use_container_width=True)
else:
    st.info("📁 Upload a CSV or Excel file to begin.")



         




