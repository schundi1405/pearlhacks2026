# model.py
import pandas as pd
import numpy as np
from utils import load_transactions


def forecast_next_6_months():

    df = load_transactions()
    if df.empty:
        return None, None, None

    # Signed amounts (income positive, expense negative)
    df["signed_amount"] = df.apply(
        lambda r: r["amount"] if r["type"] == "income" else -r["amount"],
        axis=1
    )

    df = df.sort_values("date")

    # Daily cumulative balance
    df["cumulative_balance"] = df["signed_amount"].cumsum()

    # Numeric time index (days since first date)
    df["t"] = (df["date"] - df["date"].min()).dt.days

    X = df["t"].values
    y = df["cumulative_balance"].values

    # ---- Polynomial Regression (degree 3) ----
    degree = 3
    coeffs = np.polyfit(X, y, degree)
    poly_model = np.poly1d(coeffs)

    # Predict next 6 months (approx 180 days)
    last_day = df["t"].max()
    future_days = np.arange(last_day + 1, last_day + 181)

    future_dates = pd.date_range(
        df["date"].max() + pd.Timedelta(days=1),
        periods=180,
        freq="D"
    )

    predictions = poly_model(future_days)

    forecast_df = pd.DataFrame({
        "date": future_dates,
        "predicted_balance": predictions
    })

    # ---- Category influence analysis ----
    expense_df = df[df["type"] == "expense"].copy()
    category_totals = (
        expense_df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    top_category = category_totals.idxmax()
    top_value = category_totals.max()

    trend_direction = "increasing" if coeffs[0] > 0 else "decreasing"

    explanation = (
    f"The model detects a {trend_direction} balance trajectory. "
    f"The largest contributor to spending is '{top_category}' "
    f"(total: ${top_value:.2f}). "
    f"The polynomial model captures curvature in spending behavior "
    f"rather than assuming a straight-line trend."
)

    return df, forecast_df, explanation