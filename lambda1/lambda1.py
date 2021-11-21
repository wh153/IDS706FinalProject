import pandas as pd
import boto3
import botocore
import time
import datetime
from polygon import RESTClient

# SETUP LOGGING
import logging
from pythonjsonlogger import jsonlogger

LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
LOG.addHandler(logHandler)

# Start of Script

dynamodb = boto3.resource('dynamodb')
dynamoTable = dynamodb.Table('stockprice')

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


def get_price():
    """[extract ticker, open price, close price, high price, low price, and volumn]"""
    key = "CG0mfIrTZlytZFDyMr1kOGcIpNtj4HpT"

    with RESTClient(key) as client:
        start_time = "2021-11-16"
        # end_time = "2021-11-16"
        end_time = get_current_time_local_time_zone()
        response = client.stocks_equities_aggregates(
            "AAPL", 1, "minute", start_time, end_time, unadjusted=False
        )

        ticker = response.ticker
        
        prices = pd.DataFrame.from_dict(response.results)
        prices.rename(columns = {
            't':'timestamp',
            'o':'open',
            'c':'close',
            'h':'high',
            'l':'low',
            'v':'volume',
            'vw':'volume_weighted_price',
            'n':'number_of_trades'
        },
        inplace=True)
        prices['time_str'] = prices.timestamp.apply(lambda x: timestring_to_datetime(x))
        prices.drop(columns=['a','op'], inplace=True)

        return prices


def write_to_dynamo(df):
    """Put Pandas DF to dynamodb"""
    for idx, row in df.iterrows():
        ticker = str[row[0]]
        time_str = str(row[1])
        timestamp = time.mktime(datetime.datetime.strptime(time_str,"%Y-%m-%d").timetuple())
        op = str(row[2])
        cl = str(row[3])
        hi = str(row[4])
        lo = str(row[5])
        vl = str(row[6])
        
    dynamoTable.put_item(
        Item = {
            'ticker': ticker,
            'time': timestamp,
            'time_str': time_str,
            'open': op,
            'close': cl,
            'high': hi,
            'low': lo,
            'volume': vl
        })
    
    log_dynamo_msg = (f"Put price of {ticker} at {time_str} into table.")
    LOG.info(log_dynamo_msg)
        
def lambda_handler(event, context):
    """Entry point for labmda"""
    
    """function for pulling stock price and cleaning data"""
    
    write_to_dynamo(df)