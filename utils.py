import pandas as pd
import torch


def load_and_clean_data(uploaded_file):
    df = pd.read_csv(uploaded_file, sep="\t", header=None)

    df.columns = [
        "posted_date",
        "transaction_date",
        "amount",
        "category",
        "type"
    ]

    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace(",", "")
        .astype(float)
    )

    # Make expenses negative
    df.loc[df["type"].str.lower() == "expense", "amount"] *= -1

    df["category"] = df["category"].str.lower().str.strip()

    df = df[["transaction_date", "category", "amount"]]
    df.rename(columns={"transaction_date": "date"}, inplace=True)

    return df


def calculate_monthly_metrics(df):
    today = pd.Timestamp.today()

    monthly_df = df[
        (df["date"].dt.month == today.month) &
        (df["date"].dt.year == today.year)
    ]

    current_balance = df["amount"].sum()

    daily_net = monthly_df.groupby("date")["amount"].sum()

    avg_daily = daily_net.mean()
    std_daily = daily_net.std()

    days_remaining = today.days_in_month - today.day

    projected_end_balance = current_balance + (avg_daily * days_remaining)

    return current_balance, projected_end_balance, avg_daily, std_daily, days_remaining


def calculate_risk(current_balance, mean, std, days_remaining, sims=3000):
    if pd.isna(std) or std == 0:
        return 0.0

    samples = torch.normal(mean, std, size=(sims, days_remaining))
    totals = samples.sum(dim=1)
    future_balances = current_balance + totals

    risk = (future_balances < 0).float().mean().item()
    return risk