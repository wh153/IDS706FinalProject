# Real Time Apple Stock Price Prediction Dash Web Application 
[![CI/CD](https://github.com/wh153/IDS706FinalProject/actions/workflows/CI&CD.yml/badge.svg)](https://github.com/wh153/IDS706FinalProject/actions/workflows/CI&CD.yml)

The project aimed to take advantage of the cloud technologies and platforms to build a data engineering pipeline for predicting stock prices. The application can be accessed at: http://3.16.218.189/.

## Architecture
The application consists of three major parts:
1. Retrieving and Storing Data
2. Predicting Stock Prices
3. Interfacing with Users through Dash and Docker

The overall architecture of the application is as follows:

<img width="667" alt="Workflow Fig" src="https://user-images.githubusercontent.com/89489224/145728037-3a7956f0-120a-4615-98d7-18b16b746e23.png">

### 1. Retrieving and Storing Data
We use real-time data down to the minute for this project. We obtain data is from the Polygon API (https://polygon.io/). The API is called with RESTful architectural style. We only pulled price for Apple, Inc. (AAPL) for this specific application, but more tickers can be included easily. We used the free-tier Polygon API, so the data pulled and therefore the predictions shown in the front end have a one-day delay, albeit they are still refreshed in "real-time". However, the application is capable of working with actual real-time data instantaneously once we upgrade to a paid-tier Polygon API.

To automatically pull the newest data, we built a Lambda Function that is triggered by a CloudWatch Event every minute. The code for the Lambda function is located at `lambda1/lambda_function.py`, and its dependencies are specified in `lambda1/requirements.txt`. The Lambda Function steps through several processes every time it is triggered:
- It takes note of data that has been stored
- It pulls data that is not in storage using the Polygon API
- It cleans the pulled data
- Finally, it sends the newly pulled data to a dedicated table in Dynamo DB

Logging is set up for major steps to help with monitoring and debugging.

### 2. Predicting Stock Prices
Stock price prediction is a time-series regression problem. After testing multiple models, we chose to use the Prophet model developed by Facebook for this project. The Facebook prophet model is able to analyze seasonality trends and it also requires the least number of features in order to give predictions on future stock prices. It returned more accurate predictions than AR, MA, or ARIMA models. The Prophet model is also robust against the shifting trends, a nice-to-have feature when it comes to predicting stock prices. 

Considering the complexity of time series modeling and the amount of data used, the model runs reasonably fast and is fully automated. Dataset is fit to the model under 2 minutes and predictions are made instantly. Fine-tuning the model in future iterations of the project is quite easy, as there are only a select few parameters to be adjusted. As such, it fits well with the philosophy of cloud computing. What is more, Prophet model also supports built-in methods for plotting and user interations that a traditional statsmodel library doesn't support. 


### 3. Interfacing with Users through Dash and Docker
#### Front End Application Built with Dash
We built a front end using the `dash` package in Python. The code for the dash application can be found at `lamda2_docker/dash_app.py`. Besides dependent packages, the dash application calls two custom methods - `lambda2_docker/lambda_function.py` to pull data and run model, and `lambda2_docker/clean_and_plot.py` to create the objects used in the application.

A screenshot of the front end in its initial state is shown below:

![image](https://user-images.githubusercontent.com/37159376/145722721-e2259585-3ab3-44c0-8d2c-5ff8bc7a3ff7.png)

The user interacts with the application by predicting the "Predict" button. When the button is clicked, several processes take place in the background:
1. Pull price data for the latest few thousand minutes as training data
    - This is equivalent to 5-7 trading days, subject to variation depending on the amount of pre- and post-market activities. However, trading days are artificial so we don't need to worry about having the training data start at exactly the beginning of a trading day
2. Run Prophet model on the training data, then predict prices for the next 30 minutes
3. Display training data in blue and predicted prices in red in as a line plot
4. Display predicted prices for each minute in a data table below the "Predict" button

A screenshot of the expected result is shown below:

![image](https://user-images.githubusercontent.com/37159376/145723229-3c2bd0cf-fcb7-4887-a501-16c96a38388e.png)


#### Docker Image Hosted on AWS ECS
The dash application and its dependencies are containerized as a Docker image to enable easy accessibility to the application. The Dockerfile to build the image can be found at `lambda2_docker/Dockerfile`. To make sure the application is always availble to people in every corner of the world, we hosted the Docker image on AWS ECS using a Fargate instance. Fargate instances are easy to set up, require low maintenance, and charge very little fees, which are great features for a straightforward application like this one. 

The application can be accessed at: http://3.16.218.189/.

## Continuous Integration and Secret Protection
Github Actions is used for continuous integration. It is realized by the YML file. The CI workflow is triggered by any push actions. In the CI workflow, the packages, and libraries requirements are checked, the codes are lint and checked to be in good formats, and file integrity is tested using Pytest.

Our API keys and other secrets are protected by Github Secrets. They were written in the YML file as environmental variables and then get called in the Python scripts.
