# Real Time Apple Stock Price Prediction Dash Web Application 
[![CI/CD](https://github.com/wh153/IDS706FinalProject/actions/workflows/CI&CD.yml/badge.svg)](https://github.com/wh153/IDS706FinalProject/actions/workflows/CI&CD.yml)

The project aimed to take advantage of the cloud technologies and platforms to build a data engineering pipeline for predicting stock prices. The application consists of three major parts:

1. Retrieving and Storing Data
2. Predicting Stock Prices
3. Interfacing with Users with Dash and Docker Container

The overall workflow is as follows:

![image](https://user-images.githubusercontent.com/89489224/145718732-08271fa2-0278-4525-90ad-4689170904d5.png)

## 1. Retrieving and Storing Data
We use real-time data down to the minute for this project. We obtain data is from the Polygon API (https://polygon.io/). The API is called with RESTful architectural style. We only pulled price for Apple, Inc. (AAPL) for this specific application, but more tickers can be included easily.

To automatically pull the newest data, we built a Lambda Function that is triggered by a CloudWatch Event every minute. The Lambda Function steps through several processes every time it is triggered:
- It takes note of data that has been stored
- It pulls data that is not in storage using the Polygon API
- It cleans the pulled data
- Finally, it sends the newly pulled data to a dedicated table in Dynamo DB

Logging is set up for major steps to help with monitoring and debugging.

## 2. Predicting Stock Prices
Stock predicting is a time-series regression problem. Facebook Prophet model is adopted in the project. It achieves a better result than the AR model, the MA model, and the ARIMA model. The Prophet model is also robust to the shifting trends. The model runs fast and is fully automated. It is also easy to fine-tune the model. So, it fits well in the philosophy of cloud computing.

## 3. Interfacing with Users with Dash and Docker Container
The result is visualized by an interactive plot with Dash. By clicking the "predict" button, new data is retrieved and the model is updated. Then, the new plot is shown in the front-end.

Docker is used for encapsulation. Our application is contained by Docker and held by EC2.

### Continuous integration and Secret Protection
Github Actions is used for continuous integration. It is realized by the YML file. The CI workflow is triggered by any push actions. In the CI workflow, the packages, and libraries requirements are checked, the codes are lint and checked to be in good formats, and file integrity is tested using Pytest.

Our API keys and other secrets are protected by Github Secrets. They were written in the YML file as environmental variables and then get called in the Python scripts.
