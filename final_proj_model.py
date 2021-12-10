#!/usr/bin/env python
# coding: utf-8

# In[25]:


import gzip
import json
import pandas as pd
import datetime
from fbprophet import Prophet
from fbprophet.plot import plot_plotly
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.offline as py

py.init_notebook_mode()
get_ipython().run_line_magic("matplotlib", "inline")
from fbprophet.plot import plot_plotly, plot_components_plotly


# In[26]:


def clean_data(json_gz_file) -> pd.DataFrame:
    #### need to change this part when using dynamodb data ########
    with gzip.open(json_gz_file, "r") as f:
        data = f.read().decode("utf-8")
    ###############################################################
    s = "[" + ",".join(data.rstrip().split("\n")) + "]"
    df = pd.read_json(s)
    ticker = []
    time = []
    low = []
    time_str = []
    open_ = []
    volume = []
    high = []
    close = []
    for dictionary in df.Item:
        ticker.append(dictionary["ticker"]["S"])
        time.append(int(dictionary["time"]["N"]))
        open_.append(float(dictionary["open"]["N"]))
        close.append(float(dictionary["close"]["N"]))
        high.append(float(dictionary["high"]["N"]))
        low.append(float(dictionary["low"]["N"]))
        volume.append(float(dictionary["volume"]["N"]))
    df_cleaned = pd.DataFrame(
        {
            "ticker": ticker,
            "time": time,
            "open": open_,
            "close": close,
            "high": high,
            "low": low,
            "volume": volume,
        }
    )
    df_cleaned["time"] = pd.to_datetime(df_cleaned["time"], unit="s")
    df_cleaned.sort_values(by="time", ascending=True, inplace=True)
    df_cleaned.reset_index(drop=True, inplace=True)
    # df_cleaned = df_cleaned.set_index('time')
    # df_cleaned = df_cleaned.groupby(pd.Grouper(freq="H")).mean()
    # df_cleaned.reset_index(inplace=True)
    df_cleaned.dropna(inplace=True)
    df_select = df_cleaned[["time", "close", "volume", "high", "low", "open"]]
    df_select = df_select.rename(
        columns={
            "time": "ds",
            "close": "y",
            "volume": "volume",
            "high": "high",
            "low": "low",
            "open": "open",
        }
    )
    return df_select


# In[27]:


df_select = clean_data("w4w22vvpgiymhgr475umvp256a.json.gz")


# In[56]:


def predict(data):
    prophet_model = Prophet()
    prophet_model.fit(df_select[-3000:-1])
    # future 1 month prediction
    forecast = prophet_model.predict(
        prophet_model.make_future_dataframe(periods=30, freq="min")
    )
    return prophet_model, forecast


# In[57]:


prophet_model, forecast = predict(df_select)


# In[58]:


def save_prediction(forecast):
    forecast.to_csv("forecast.csv")


# In[59]:


def plot(prophet_model, forecast):
    return plot_plotly(prophet_model, forecast)


# In[60]:


plot(prophet_model, forecast)


# In[61]:


save_prediction(forecast)
