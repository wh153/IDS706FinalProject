import dash
import dash_html_components as html
import plotly.graph_objects as go
import dash_core_components as dcc
import plotly.express as px
from dash.dependencies import Input, Output
import pandas as pd

from lambda_function import main as run_model

import os
import sys


app = dash.Dash()


def draw_graphs(df):
    fig = px.line(
        df,
        x="ds",
        y="yhat",
        labels={"x": "Date-Time", "y": "Apple Stock Price"},
        title="Apple Stock Price",
        color_discrete_sequence=["red"],
    )

    return fig


# prophet_model, forecast = run_model()
df = pd.read_csv("forecast.csv")
fig = draw_graphs(df)


button_style = {
    "border": "none",
    "color": "black",
    "padding": "13px 27px",
    "text-align": "center",
    "text-decoration": "none",
    "font-size": "17px",
    "align": "center",
}


def app_layout(df):
    app.layout = html.Div(
        [
            html.H1(
                "Stock Price Predictions",
                style={"text-align": "center", "color": "black"},
            ),
            html.Div(
                [
                    dcc.Graph(id="my_bee_map", figure=fig),
                ],
                style={"height": "50%"},
            ),
            html.Div(
                [
                    html.Button(
                        "Restart", id="btn-nclicks-1", n_clicks=0, style=button_style
                    ),
                    html.Button(
                        "Predict", id="btn-nclicks-2", n_clicks=0, style=button_style
                    ),
                ],
                style=button_style,
            ),
            html.Div(
                id="container-button-timestamp",
                style={
                    "text-align": "center",
                    "color": "black",
                    "fontSize": 40,
                    "margin": "auto",
                },
            ),
        ],
        style={
            "position": "absolute",
            "width": "100%",
            "height": "100%",
            "top": "0px",
            "left": "0px",
        },
    )


app_layout(df)


@app.callback(
    Output("container-button-timestamp", "children"),
    [Input("btn-nclicks-1", "n_clicks"), Input("btn-nclicks-2", "n_clicks")],
)
def displayClick(btn1, btn2):
    changed_id = [p["prop_id"] for p in dash.callback_context.triggered][0]
    print(changed_id)
    msg = str()

    if "btn-nclicks-2.n_clicks" == changed_id:
        print("YES")
        new_model, new_df = run_model()
        fig = draw_graphs(new_df)
        app_layout(new_df)

    elif "btn-nclicks-1.n_clicks" == changed_id:
        print("YES")
        os.execl(sys.executable, sys.executable, *sys.argv)
    else:
        print("")


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8050, debug=True)
