import numpy as np
import pandas as pd
import time
import datetime
import boto3
import botocore
from boto3.dynamodb.conditions import Key
import awswrangler as wr
from polygon import RESTClient
from decimal import Decimal


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
KEYS = pd.read_csv("C:\\Users\\Robert\\Desktop\\rootkey.csv", header=None)
ACCESS_KEY = KEYS.iloc[0, 1]
SECRET_KEY = KEYS.iloc[1, 1]
boto3 = boto3.Session(
    aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=REGION
)

dynamodb = boto3.resource("dynamodb")
dynamoTable = dynamodb.Table("stockprice")

# Clean prices history data
def clean_historical_data(df):
    """clean historical data"""
    # rename columns
    df.rename(
        columns={"datetime": "time_str", "volumn": "volume", "datetime_int": "time"},
        inplace=True,
    )

    # add volume_weighted_price column
    # we probably don't need this, but it's in the lambda
    df["volume_weighted_price"] = np.NaN

    # sort time time
    df.sort_values(by="time", inplace=True)

    # divide timestamp by 1000
    df["time"] = df.time / 1000

    # reset index
    df.reset_index(inplace=True, drop=True)


def query_last_entry(ticker):
    """query latest time of the ticker"""
    response = dynamoTable.query(
        ProjectionExpression="time_str, #ts",
        ExpressionAttributeNames={"#ts": "time"},
        KeyConditionExpression=Key("ticker").eq(ticker),
        ScanIndexForward=False,
        Limit=1,
    )

    last_time = response["Items"][0]["time"]
    return last_time


# functions to help us load
def float_to_decimal(num):
    """
    helper function to convert number to decimal
    to be used in write_chunk_to_dynamo()
    """
    return Decimal(str(num))


def write_chunk_to_dynamo(df):
    """
    write pandas df to DDB in chunks
    this is much faster than writing by row
    """
    logging_helper = (
        df.groupby("ticker").agg({"time": [max, min]})["time"].reset_index()
    )
    logging_helper.rename(columns={"max": "max_time", "min": "min_time"}, inplace=True)

    # reorder columns
    cols = [
        "ticker",
        "time",
        "close",
        "high",
        "low",
        "open",
        "time_str",
        "volume",
        "volume_weighted_price",
    ]
    df = df[cols]

    # load df to dynamodb
    # 1. convert float to decimal because DynamoDB cannot handle float
    for i in df.columns:
        datatype = df[i].dtype
        if datatype == "float64":
            df[i] = df[i].apply(float_to_decimal)
    # 2. write to dynamodb
    wr.dynamodb.put_df(df=df, table_name="stockprice", boto3_session=boto3)

    for _, row in logging_helper.iterrows():
        log_dynamo_msg = (
            f"Put price of {row[0]} from time {row[2]} to time {row[1]} into table."
        )
        LOG.info(log_dynamo_msg)


def write_to_dynamo(df):
    """Put Pandas DF to dynamodb in 50 row chunks"""
    n = 200
    start_idx = 0
    end_idx = min(df.shape[0], n)
    while start_idx < len(df):
        df_to_load = df.iloc[start_idx:end_idx, :]
        write_chunk_to_dynamo(df_to_load)

        start_idx = end_idx
        end_idx = min(df.shape[0], start_idx + n)

        # sleep for 1 sec so that we don't get throttled
        time.sleep(1)

        pass
    pass


if __name__ == "__main__":
    prices = pd.read_csv(
        "C:\\Users\\Robert\\Documents\\GitHub\\IDS706FinalProject\\price.csv"
    )
    clean_historical_data(prices)

    last_time = query_last_entry("AAPL")
    prices = prices[prices.time >= last_time]
    prices.reset_index(inplace=True, drop=True)

    write_to_dynamo(prices)
