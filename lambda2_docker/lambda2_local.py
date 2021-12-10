import pandas as pd
import time
import datetime
import pytz
import boto3
from boto3.dynamodb.conditions import Key
from io import StringIO
import json
from prophet import Prophet
from prophet.serialize import model_to_json, model_from_json


# SETUP LOGGING
import logging
from pythonjsonlogger import jsonlogger

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
LOG.addHandler(logHandler)


# Start boto3 session
REGION = "us-east-2"
KEYS = pd.read_csv("rootkey.csv", header=None)
ACCESS_KEY = KEYS.iloc[0, 1]
SECRET_KEY = KEYS.iloc[1, 1]
boto3 = boto3.Session(
    aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=REGION
)


# Start DDB
dynamodb = boto3.resource("dynamodb")
dynamoTable = dynamodb.Table("stockprice")


# Get Data from DDB
def query_data(ticker):
    """
    query last 5000 rows of data
    returns a pandas DF
    """
    response = dynamoTable.query(
        ProjectionExpression="#ts, ticker, #op, #cl, high, low, volume",
        ExpressionAttributeNames={"#ts": "time", "#op": "open", "#cl": "close"},
        KeyConditionExpression=Key("ticker").eq(ticker),
        ScanIndexForward=False,
        Limit=4500,
    )

    df = pd.DataFrame(response["Items"])

    return df


# Clean data
def timestring_to_datetime(timestring):
    """[transform into the datetime type]

    Args:
        ts ([int]): [time integer]

    Returns:
        [datetime]: [datetime object]
    """
    t = datetime.datetime.utcfromtimestamp(timestring).replace(tzinfo=pytz.utc)
    t = t.astimezone(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M")
    return t


def truncate_most_recent_day(df):
    """
    truncate price data for the most recent day
    predictions will have a 1-day lag, but will be in "real-time" (i.e. changing)

    this is because we get data with at end of day with the free API
    """
    now = int(time.time())
    yesterday = now - 86400
    df = df[df.time <= yesterday]

    # logging
    if LOG.hasHandlers():
        LOG.handlers.clear()
        LOG.addHandler(logHandler)

    # get max and min time queried for each ticker
    logging_helper = (
        df.groupby("ticker").agg({"time": [max, min]})["time"].reset_index()
    )
    logging_helper.rename(columns={"max": "max_time", "min": "min_time"}, inplace=True)
    # get row counts for each ticker
    row_ct = df.groupby("ticker").count().reset_index().iloc[:, 0:2]
    row_ct.rename(columns={"low": "rows"})

    logging_helper = pd.merge(logging_helper, row_ct, on="ticker")
    for _, row in logging_helper.iterrows():
        log_dynamo_msg = f"After truncation, data for {row[0]} ranges from min time {row[2]} to max time {row[1]}. {row[3]} rows"
        LOG.info(log_dynamo_msg)

    return df


def clean_data(df) -> pd.DataFrame:
    """
    cleans data to make it ready for FB prophet
    """
    df_clean = df
    df_clean["time"] = pd.to_datetime(
        df.time.astype(int).apply(lambda x: timestring_to_datetime(x))
    )
    df_clean.sort_values(by="time", ascending=True, inplace=True)
    df_clean.reset_index(drop=True, inplace=True)
    df_clean.dropna(inplace=True)
    df_clean = df_clean.astype(
        {
            "close": "float64",
            "volume": "float64",
            "high": "float64",
            "low": "float64",
            "open": "float64",
        }
    )
    df_clean = df_clean[["time", "close", "volume", "high", "low", "open"]]
    df_clean = df_clean.rename(
        columns={
            "time": "ds",
            "close": "y",
            "volume": "volume",
            "high": "high",
            "low": "low",
            "open": "open",
        }
    )
    return df_clean


# Run model
def predict(df):
    # change logging level so that we don't get so many modeling logging msg
    LOG.setLevel(logging.ERROR)

    # run model
    prophet_model = Prophet()
    prophet_model.fit(df)
    # future 30 minute prediction
    forecast = prophet_model.predict(
        prophet_model.make_future_dataframe(periods=30, freq="min")
    )

    # logging
    if LOG.hasHandlers():
        LOG.handlers.clear()
        LOG.addHandler(logHandler)

    LOG.setLevel(logging.INFO)
    log_model_msg = f"Finished running model."
    LOG.info(log_model_msg)
    return prophet_model, forecast


# Start S3
s3 = boto3.resource("s3")
bucket = "ids706stockpredictions"

# Store model as json in S3
def save_model_to_s3(prophet_model):
    """save prophet model to s3 bucket"""
    # save model
    serialized_model = json.dumps(model_to_json(prophet_model)).encode("UTF-8")

    # place model in s3
    s3.Object(bucket, "stock_prediction_model.json").put(Body=bytes(serialized_model))


def save_forecast_to_s3(df):
    """
    put predictions into s3 bucket as csv file
    also name the csv based on the furthest time of prediction
    """
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)

    # furthest_time_predicted = df.sort_values("time", ascending=False).time[0]
    # csv_name = "prediction_through_" + str(furthest_time_predicted)
    s3.Object(bucket, "stock_forecast.csv").put(Body=csv_buffer.getvalue())


def main():
    """Entry point for labmda"""
    ticker = "AAPL"
    df = query_data(ticker)
    print("Finished running: query_data")
    df = truncate_most_recent_day(df)
    print("Finished running: trudncate_most_recent_day")

    # clean data and generate model
    df_clean = clean_data(df)
    print("Finished running: clean_data")
    prophet_model, forecast = predict(df_clean)
    print("Finished running: predict")

    # save to s3
    # save_model_to_s3(prophet_model)
    # print('Finished running: save_model_to_s3')
    # save_forecast_to_s3(forecast)
    # print('Finished running: save_forecast_to_s3')
    return prophet_model, forecast


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
    # function for stock price data
