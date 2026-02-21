# utils.py
import pandas as pd

CSV_FILE = "sample_data_sheet1.csv"

def load_transactions():
    """Load CSV and parse dates"""
    df = pd.read_csv(CSV_FILE, parse_dates=['date'])
    return df

def add_transaction(date, amount, category, t_type):
    """Add a transaction in chronological order"""
    df = load_transactions()
    
    new_row = pd.DataFrame({
        'date': [pd.to_datetime(date)],
        'amount': [float(amount)],
        'category': [category],
        'type': [t_type]
    })
    
    df = pd.concat([df, new_row], ignore_index=True)
    df = df.sort_values('date').reset_index(drop=True)
    df.to_csv(CSV_FILE, index=False)
    return df

def spending_by_weekday():
    """
    Returns:
        weekday_avg (DataFrame): average expense per weekday (ordered)
        max_day (Series): row containing highest average spending weekday
    """
    df = load_transactions()

    if df.empty:
        return None, None

    # Keep only expenses
    expenses = df[df["type"] == "expense"].copy()

    if expenses.empty:
        return None, None

    # Ensure numeric
    expenses["amount"] = expenses["amount"].astype(float)

    # Extract weekday name
    expenses["weekday"] = expenses["date"].dt.day_name()

    # Compute average spending per weekday
    weekday_avg = (
        expenses
        .groupby("weekday")["amount"]
        .mean()
        .reset_index()
    )

    # Proper weekday order
    weekday_order = [
        "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday", "Sunday"
    ]

    weekday_avg["weekday"] = pd.Categorical(
        weekday_avg["weekday"],
        categories=weekday_order,
        ordered=True
    )

    weekday_avg = weekday_avg.sort_values("weekday")

    # Find highest average spending day
    max_day = weekday_avg.loc[
        weekday_avg["amount"].idxmax()
    ]

    min_day = weekday_avg.loc[
        weekday_avg["amount"].idxmin()
    ]

    return weekday_avg, max_day, min_day