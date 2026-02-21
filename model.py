# model.py
import torch
import torch.nn as nn
import pandas as pd
from utils import load_transactions

class AmountPredictor(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = nn.Linear(1, 1)  # amount ~ date ordinal

    def forward(self, x):
        return self.model(x)

def train_model(epochs=200, lr=0.01):
    df = load_transactions()
    df['date_ordinal'] = df['date'].map(lambda x: x.toordinal())
    
    X = torch.tensor(df['date_ordinal'].values, dtype=torch.float32).unsqueeze(1)
    y = torch.tensor(df['amount'].values, dtype=torch.float32).unsqueeze(1)
    
    model = AmountPredictor()
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    for epoch in range(epochs):
        optimizer.zero_grad()
        y_pred = model(X)
        loss = criterion(y_pred, y)
        loss.backward()
        optimizer.step()
    
    return model