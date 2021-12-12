import pandas as pd
import plotly.express as px
from lambda_function import main as run_model


def create_df_for_plot(df_clean, forecast):
    cleaned_forecast = forecast
    cleaned_forecast.iloc[:-30,[2]] = df_clean[['y']]
    cleaned_forecast.iloc[:-30,[3]] = df_clean[['y']]
    cleaned_forecast.iloc[:-30,[-1]] = df_clean[['y']]
    cleaned_forecast['Actual or Predicted'] = 'Actual Price'
    cleaned_forecast.iloc[-30:,-1] = 'Predicted Price'
    cleaned_forecast = cleaned_forecast.rename(columns={"ds":"Date Time", "yhat": "Price"})
    return cleaned_forecast


def draw_graphs(df):
    fig = px.line(
        df,
        x="Date Time",
        y="Price",
        labels={"x": "Date Time", "y": "Price"},
        title="Apple Stock Price",
        color='Actual or Predicted'
    )
    fig.update_xaxes(rangeslider_visible=True)
    return fig


def update_graph_and_table():
    df_clean, prophet_model, forecast = run_model()
    cleaned_forecast = create_df_for_plot(df_clean, forecast)
    fig = draw_graphs(cleaned_forecast)
    df_for_table=cleaned_forecast.loc[cleaned_forecast['Actual or Predicted'] == "Predicted Price", ["Date Time", "Price"]].rename(columns={"Price": "Predicted Price"})
    return fig, df_for_table

