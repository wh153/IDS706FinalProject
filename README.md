# Real Time Apple Stock Price Prediction Dash Web Application 
[![CI/CD](https://github.com/wh153/IDS706FinalProject/actions/workflows/CI&CD.yml/badge.svg)](https://github.com/wh153/IDS706FinalProject/actions/workflows/CI&CD.yml)

The project aimed to take advantage of the cloud technologies and platforms to build a data engineering pipeline for predicting stock prices. Three major parts consist of the main workflow: 1. Retrieving and Storing the Data, 2. Building Prediction Model, 3. Front-end with Dash and Docker Container.

## 1. Retrieving and Storing the Data
In the project, real-time data is adopted. We take Apple as an example. The data is from the Polygon API (https://polygon.io/). The API is called with RESTful architectural style.

A lambda function triggered by a Cloud-Watch is built for retrieving data every minute using RESTful API. The  Cloud-Watch Log is used for holding the logging information. Then, the retrieved data is stored in a Dynamo DB that is also done by the lambda function.

## 2. Building Prediction Model

## 3. Front-end with Dash and Docker Container
