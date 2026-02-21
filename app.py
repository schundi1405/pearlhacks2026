# app.py
import streamlit as st
from datetime import date as dt_date
from utils import add_transaction, load_transactions, spending_by_weekday
from model import forecast_next_6_months
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

# --- 3. Cumulative balance visualization ---
st.subheader("Cumulative Balance Over Time")

if not df.empty:
    # Convert amounts to positive/negative based on type
    df['signed_amount'] = df.apply(
        lambda row: row['amount'] if row['type']=='income' else -row['amount'], axis=1
    )
    
    # Sort by date
    df = df.sort_values('date')
    
    # Compute cumulative balance
    df['cumulative_balance'] = df['signed_amount'].cumsum()
    
    # Line chart with dates on x-axis, cumulative balance on y-axis
    st.line_chart(data=df.set_index('date')['cumulative_balance'])
else:
    st.info("No transactions yet to display.")


st.subheader("Spending by Day of Week")

weekday_totals, max_day, min_day = spending_by_weekday()

if weekday_totals is not None:
    st.bar_chart(
        data=weekday_totals.set_index("weekday")["amount"]
    )

    st.write(
        f"Highest Spending Day on Average: **{max_day['weekday']}** "
        f"(${max_day['amount']:.2f})"
    )

    st.write(
        f"Lowest Spending Day on Average: **{min_day['weekday']}** "
        f"(${min_day['amount']:.2f})"
    )
else:
    st.info("Not enough expense data yet.")


# predict spending
st.subheader("Balance Forecast (Next 6 Months)")

actual_df, forecast_df, explanation = forecast_next_6_months()

if actual_df is not None:

    actual_plot = actual_df[["date", "cumulative_balance"]].set_index("date")
    forecast_plot = forecast_df.set_index("date")

    combined = actual_plot.join(forecast_plot, how="outer")

    st.line_chart(combined)

    st.write("### Why this prediction?")
    st.write(explanation)

else:
    st.info("Not enough data to forecast.")
