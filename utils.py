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