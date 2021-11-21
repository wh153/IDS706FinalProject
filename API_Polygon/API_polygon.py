from polygon import RESTClient
import datetime
import time
import csv

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

    path = "price.csv"
    with open(path, "w") as f:
        csv_write = csv.writer(f)
        csv_header = [
            "ticker",
            "datetime",
            "datetime_int",
            "open",
            "close",
            "high",
            "low",
            "volumn",
        ]
        csv_write.writerow(csv_header)

    with RESTClient(key) as client:
        iteration = 0
        interval = 365
        seen = set()
        while iteration < interval:
            delta = datetime.timedelta(days=-iteration - 1)
            # end_time = "2021-11-16"
            end_time = datetime.datetime.now() + delta
            start_time = end_time + datetime.timedelta(days=-1)

            end_time = end_time.strftime("%Y-%m-%d")
            start_time = start_time.strftime("%Y-%m-%d")

            response = client.stocks_equities_aggregates(
                "AAPL", 1, "minute", start_time, end_time, unadjusted=False
            )

            ticker = response.ticker
            print("the ticker is:", ticker)

            with open(path, "a+") as f:
                csv_write = csv.writer(f)
                for result in response.results:
                    # print("time: ", result["t"])
                    time_int = result["t"]
                    if time_int in seen:
                        continue
                    seen.add(time_int)
                    dt = timestring_to_datetime(time_int)
                    op, cl = result["o"], result["c"]
                    high, low = result["h"], result["l"]
                    vol = result["v"]
                    # print(f"{dt}\n\tO: {op}\n\tH: {high}\n\tL: {low}\n\tC: {cl}\n\tV: {vol}")
                    temp = [ticker, dt, time_int, op, cl, high, low, vol]
                    csv_write.writerow(temp)
            iteration += 1
            time.sleep(15)


if __name__ == "__main__":
    main()
