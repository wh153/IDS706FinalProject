from polygon import RESTClient
import datetime
import time

"""
def main():
    key = "API"

    with RESTClient(key) as client:
        resp = client.stocks_equities_daily_open_close("AAPL", "2021-11-11")
        print(
            f"On: {resp.from_} Apple opened at {resp.open} and closed at {resp.close}"
        )


if __name__ == "__main__":
    main()
"""


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


def main():
    """[extract ticker, open price, close price, high price, low price, and volumn]"""
    key = "CG0mfIrTZlytZFDyMr1kOGcIpNtj4HpT"

    with RESTClient(key) as client:
        start_time = "2021-11-16"
        # end_time = "2021-11-16"
        end_time = get_current_time_local_time_zone()
        response = client.stocks_equities_aggregates(
            "AAPL", 5, "minute", start_time, end_time, unadjusted=False
        )

        ticker = response.ticker
        print("the ticker is:", ticker)

        for result in response.results:
            print("time: ", result["t"])
            time_int = result["t"]
            dt = timestring_to_datetime(time_int)
            op, cl = result["o"], result["c"]
            high, low = result["h"], result["l"]
            vol = result["v"]
            print(f"{dt}\n\tO: {op}\n\tH: {high}\n\tL: {low}\n\tC: {cl}\n\tV: {vol}")


if __name__ == "__main__":
    main()
