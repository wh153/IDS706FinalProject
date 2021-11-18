import pandas as pd
import boto3
import botocore
import time
import datetime

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