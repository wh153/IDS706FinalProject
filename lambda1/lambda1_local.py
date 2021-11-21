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
ACCESS_KEY = KEYS.iloc[0,1]
SECRET_KEY = KEYS.iloc[1,1]
boto3 = boto3.Session(
    aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=REGION
)


# Start of Script
dynamodb = boto3.resource("dynamodb")
dynamoTable = dynamodb.Table("stockprice")
ticker = "AAPL"

# script to pull stock price from Polygon API
def get_current_time_local_time_zone():
    """[get_current_time_local_time_zone]

    Returns:
        [string]: ["2021-11-15"]
    """
    return time.strftime("%Y-%m-%d", time.localtime())


def timestring_to_datetime(timestring):
    """[transform into the datetime type]

    Args:
        ts ([int]): [time integer]

    Returns:
        [datetime]: [datetime object]
    """
    timestring /= 1000
    t = datetime.datetime.fromtimestamp(timestring).strftime("%Y-%m-%d %H:%M")
    return t


def query_last_entry(ticker):
    """query latest time of the ticker"""
    response = dynamoTable.query(
        ProjectionExpression="time_str, #ts",
        ExpressionAttributeNames={"#ts": "time"},
        KeyConditionExpression=Key("ticker").eq(ticker),
        ScanIndexForward=False,
        Limit=1,
    )

    last_time = datetime.datetime.strptime(
        response["Items"][0]["time_str"], "%Y-%m-%d %H:%M"
    )
    return last_time


def get_price(ticker):
    """[extract ticker, open price, close price, high price, low price, and volumn]"""
    key = "CG0mfIrTZlytZFDyMr1kOGcIpNtj4HpT"

    with RESTClient(key) as client:
        last_data_time = query_last_entry(ticker)
        #start_time = "2021-11-19"
        start_time = last_data_time.strftime("%Y-%m-%d")
        #end_time = "2021-11-16"
        end_time = get_current_time_local_time_zone()
        response = client.stocks_equities_aggregates(
            ticker, 1, "minute", start_time, end_time, unadjusted=False
        )

        ticker = response.ticker

        prices = pd.DataFrame.from_dict(response.results)
        prices.rename(
            columns={
                "t": "time",
                "o": "open",
                "c": "close",
                "h": "high",
                "l": "low",
                "v": "volume",
                "vw": "volume_weighted_price",
                "n": "number_of_trades",
            },
            inplace=True,
        )
        prices["time_str"] = prices.time.apply(lambda x: timestring_to_datetime(x))
        prices["time"] = prices.time / 1000
        prices["ticker"] = ticker

        # polygon API grabs data for the entire day
        # we want to filter out the data that we already have
        last_data_time_stamp = time.mktime(last_data_time.timetuple())
        prices = prices[prices.time >= last_data_time_stamp]

        return prices


# code to load pandas df to DDB in chunks
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
    n = 50
    start_idx = 0
    end_idx = min(df.shape[0], n)
    while start_idx < len(df):
        df_to_load = df.iloc[start_idx:end_idx,:]
        write_chunk_to_dynamo(df_to_load)

        start_idx = end_idx
        end_idx = min(df.shape[0], start_idx + n)

        # sleep for 1 sec so that we don't get throttled
        time.sleep(1)

        pass
    pass


def write_to_dynamo_deprecated(df):
    """Put Pandas DF to dynamodb"""
    # ensure we only get the columns we want, no extra columns
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
    for idx, row in df.iterrows():
        ticker = str(row[0])
        time_str = str(row[-3])
        time = int(row[1])
        open = str(row[5])
        close = str(row[2])
        high = str(row[3])
        low = str(row[4])
        volume = str(row[-2])
        volume_weighted = str(row[-1])

        dynamoTable.put_item(
            Item={
                "ticker": ticker,
                "time": time,
                "time_str": time_str,
                "open": open,
                "close": close,
                "high": high,
                "low": low,
                "volume": volume,
                "volume_weighted_price": volume_weighted,
            }
        )

    log_dynamo_msg = f"Put price of {ticker} at {time_str} into table."
    LOG.info(log_dynamo_msg)


def lambda_handler(event, context):
    """Entry point for labmda"""

    # function for pulling stock price and cleaning data
    ticker = "AAPL"
    prices = get_price(ticker)

    # load data to DynamoDB
    write_to_dynamo(prices)

    # logging
    logging_helper = (
        prices.groupby("ticker").agg({"time": [max, min]})["time"].reset_index()
    )
    logging_helper.rename(columns={"max": "max_time", "min": "min_time"}, inplace=True)

    for _, row in logging_helper.iterrows():
        log_dynamo_msg = (
            f"Finished loading all chunks of {row[0]}. Min time {row[2]} to max time {row[1]}."
        )
        LOG.info(log_dynamo_msg)