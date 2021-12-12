import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import pandas as pd

from clean_and_plot import draw_graphs as draw_init_graph
from clean_and_plot import update_graph_and_table


# Initialize dash and plot
app = dash.Dash()
df = pd.DataFrame(columns=["Date Time", "Price", "Actual or Predicted"])
fig = draw_init_graph(df)


# define button style
button_style = {
    "border": "none",
    "color": "black",
    "padding": "13px 27px",
    "text-align": "center",
    "text-decoration": "none",
    "font-size": "17px",
    "align": "center",
}

# define dashboard layout
app.layout = html.Div(
    [
        # title of webpage
        html.H1(
            "Stock Price Predictions",
            style={"text-align": "center", "color": "black"},
        ),
        # graph
        html.Div(
            id="graph",
            children=dcc.Graph(id="my_bee_map", figure=fig),
            style={"height": "50%"},
        ),
        # predict button
        html.Div(
            [
                html.Button(
                    "Predict", id="btn-nclicks-2", n_clicks=0, style=button_style
                ),
                dcc.Loading(
                    id="loading",
                    children=html.Div(id="loading-output"),
                    type="default",
                    style={"border": "none", "margin-top": "60px"},
                ),
            ],
            style=button_style,
        ),
        # predict button with spinner
        # html.Div(id="container-button-basic", style={"text-align": "center"}),
        # spinner
        # html.Div(
        #     dbc.Spinner(html.Div(id="loading-output")),
        # ),
        # predicted prices
        html.Div(
            id="table",
            children=dash.dash_table.DataTable(
                id="predicted-prices", columns=[], data=None
            ),
            style={
                "width": "62%",
                "margin-top": "60px",
                "margin-bottom": "80px",
                "margin-left": "auto",
                "margin-right": "auto",
            },
        ),
    ],
    style={
        # "position": "absolute",
        "width": "100%",
        "height": "100%",
        "top": "0px",
        "left": "0px",
    },
)

#
@app.callback(
    Output("graph", "children"),
    Output("table", "children"),
    Output("loading-output", "children"),
    Input("btn-nclicks-2", "n_clicks"),
)
def displayClick(n_clicks):
    changed_id = [p["prop_id"] for p in dash.callback_context.triggered][0]
    if "btn-nclicks-2" in changed_id:
        # new_df = pd.DataFrame(columns=["Date Time", "Price", "Actual or Predicted"])
        # newplot = draw_init_graph(new_df)
        # newtable = dash.dash_table.DataTable(
        #     id="predicted-prices", columns=[{"name": i, "id": i} for i in ['test']], data=None,
        #     style_cell={"textAlign": "left","align":"center"},
        # )

        newplot, df_for_table = update_graph_and_table()
        newtable = dash.dash_table.DataTable(
            id="predicted-prices",
            columns=[{"name": i, "id": i} for i in df_for_table.columns],
            data=df_for_table.to_dict("records"),
            style_cell={"textAlign": "left"},
            style_data={"color": "black", "backgroundColor": "white"},
            style_data_conditional=[
                {
                    "if": {"row_index": "odd"},
                    "backgroundColor": "rgb(220, 220, 220)",
                }
            ],
            style_header={
                "backgroundColor": "rgb(210, 210, 210)",
                "color": "black",
                "fontWeight": "bold",
            },
        )
        print("Predict button pressed {} times".format(n_clicks))

    else:
        new_df = pd.DataFrame(columns=["Date Time", "Price", "Actual or Predicted"])
        newplot = draw_init_graph(new_df)
        newtable = dash.dash_table.DataTable(
            id="predicted-prices", columns=[], data=None
        )
        print("Button not clicked yet")

    return (
        dcc.Graph(id="new-bee-plot", figure=newplot, style={"height": "50%"}),
        newtable,
        "",
    )


if __name__ == "__main__":
    app.run_server(port=80)
