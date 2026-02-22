# model.py
import pandas as pd
import numpy as np
from utils import load_transactions
from sklearn.linear_model import LinearRegression


def forecast_next_6_months():

    df = load_transactions()
    if df.empty:
        return None, None, None

    # Signed amounts
    df["signed_amount"] = df.apply(
        lambda r: r["amount"] if r["type"] == "income" else -r["amount"],
        axis=1
    )
    df = df.sort_values("date")
    df["cumulative_balance"] = df["signed_amount"].cumsum()
    df["t"] = (df["date"] - df["date"].min()).dt.days

    # Linear regression
    X = df["t"].values.reshape(-1, 1)  # days since first transaction
    y = df["cumulative_balance"].values
    model = LinearRegression()
    model.fit(X, y)

    last_day = df["t"].max()
    future_days = np.arange(last_day + 1, last_day + 181).reshape(-1, 1)
    future_dates = pd.date_range(
        df["date"].max() + pd.Timedelta(days=1),
        periods=180,
        freq="D"
    )
    predictions = model.predict(future_days)

    forecast_df = pd.DataFrame({
        "date": future_dates,
        "predicted_balance": predictions
    })

    # Top spending category
    expense_df = df[df["type"] == "expense"].copy()
    category_totals = (
        expense_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )
    if not category_totals.empty:
        top_category = category_totals.idxmax()
        top_value = category_totals.max()
    else:
        top_category = "N/A"
        top_value = 0

    trend_direction = "increasing" if model.coef_[0] > 0 else "decreasing"

    explanation = (
        f"The model detects a {trend_direction} balance trajectory. "
        f"The largest contributor to spending is '{top_category}' "
        f"(total: ${top_value:.2f}). "
        f"The linear model assumes a steady trend based on past net income."
    )

    return df, forecast_df, explanation