import pandas as pd
import time
import datetime
import pytz
import json
import boto3
import base64
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from prophet import Prophet

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
# def get_secret():

#     secret_name = "aws_access_key_1"
#     region_name = "us-east-2"

#     # Create a Secrets Manager client
#     session = boto3.session.Session()
#     client = session.client(
#         service_name='secretsmanager',
#         region_name=region_name
#     )

#     # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
#     # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
#     # We rethrow the exception by default.

#     try:
#         get_secret_value_response = client.get_secret_value(
#             SecretId=secret_name
#         )
#     except ClientError as e:
#         if e.response['Error']['Code'] == 'DecryptionFailureException':
#             # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
#             # Deal with the exception here, and/or rethrow at your discretion.
#             raise e
#         elif e.response['Error']['Code'] == 'InternalServiceErrorException':
#             # An error occurred on the server side.
#             # Deal with the exception here, and/or rethrow at your discretion.
#             raise e
#         elif e.response['Error']['Code'] == 'InvalidParameterException':
#             # You provided an invalid value for a parameter.
#             # Deal with the exception here, and/or rethrow at your discretion.
#             raise e
#         elif e.response['Error']['Code'] == 'InvalidRequestException':
#             # You provided a parameter value that is not valid for the current state of the resource.
#             # Deal with the exception here, and/or rethrow at your discretion.
#             raise e
#         elif e.response['Error']['Code'] == 'ResourceNotFoundException':
#             # We can't find the resource that you asked for.
#             # Deal with the exception here, and/or rethrow at your discretion.
#             raise e
#     else:
#         # Decrypts secret using the associated KMS CMK.
#         # Depending on whether the secret is a string or binary, one of these fields will be populated.
#         if 'SecretString' in get_secret_value_response:
#             secret = get_secret_value_response['SecretString']
#         else:
#             secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            
#     return json.loads(secret)

#secrets = get_secret()
REGION = "us-east-2"
#ACCESS_KEY = secrets['aws_access_key']
#SECRET_KEY = secrets['aws_secret_access_key']
#boto3 = boto3.Session(
#    aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY, region_name=REGION
#)


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
        Limit=6500,
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
    row_ct = df.groupby("ticker").count().reset_index().iloc[:,0:2]
    row_ct.rename(columns={'low':'rows'})

    logging_helper = pd.merge(logging_helper, row_ct, on='ticker')
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


def main():
    """Entry point"""
    ticker = "AAPL"
    df = query_data(ticker)
    #print('Finished running: query_data')
    df = truncate_most_recent_day(df)
    #print('Finished running: trudncate_most_recent_day')

    # clean data and generate model
    df_clean = clean_data(df)
    #print('Finished running: clean_data')
    prophet_model, forecast = predict(df_clean)
    #print('Finished running: predict')

    # save to s3
    # save_model_to_s3(prophet_model)
    # print('Finished running: save_model_to_s3')
    # save_forecast_to_s3(forecast)
    # print('Finished running: save_forecast_to_s3')
    return prophet_model, forecast
