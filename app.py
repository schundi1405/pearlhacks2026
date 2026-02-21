# app.py
import streamlit as st
from datetime import date as dt_date
from utils import add_transaction, load_transactions
from model import train_model
import pandas as pd
import torch

st.set_page_config(page_title="Transaction Tracker", layout="wide")
st.title("Transaction Tracker")

# --- 1. Add transaction form ---
with st.form("add_transaction_form"):
    date_input = st.date_input("Date", dt_date.today())
    amount_input = st.number_input("Amount", min_value=0.0, step=0.01)
    category_input = st.text_input("Category")
    type_input = st.selectbox("Type", ["expense", "income"])
    
    submitted = st.form_submit_button("Add Transaction")
    
    if submitted:
        df = add_transaction(date_input, amount_input, category_input, type_input)
        st.success("Transaction added!")
        st.dataframe(df)

# --- 2. Display all transactions ---
st.subheader("All Transactions")
df = load_transactions()
st.dataframe(df)

# --- 3. Monthly net amount visualization ---
st.subheader("Monthly Net Amount")

if not df.empty:
    # Convert amounts to positive/negative based on type
    df['signed_amount'] = df.apply(lambda row: row['amount'] if row['type']=='income' else -row['amount'], axis=1)
    
    # Group by month
    df['month'] = df['date'].dt.to_period('M')
    monthly = df.groupby('month')['signed_amount'].sum().reset_index()
    
    # Streamlit line chart
    st.line_chart(data=monthly.set_index('month')['signed_amount'])
else:
    st.info("No transactions yet to display.")