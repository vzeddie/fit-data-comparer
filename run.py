#!/usr/bin/python3

# General
import fitdecode
import argparse
import sys
from copy import deepcopy
from functools import reduce
import logging
# Pandas
import pandas as pd
# Plotly
import plotly.express as px
import plotly.graph_objs as go
# Plotly-Dash
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Logging setup
logf = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
log = logging.getLogger()
log.setLevel(logging.DEBUG)
# - Log to file
fhandler = logging.FileHandler("{}.log".format("dash"))
fhandler.setFormatter(logf)
log.addHandler(fhandler)
# - Stream handler to stdout
shandler = logging.StreamHandler(sys.stdout)
shandler.setFormatter(logf)
log.addHandler(shandler)

"""
TODO:
   * Heart rate zones
   * GPS map with color lines
"""

def main():
    pass

# XREF: https://meterstomiles.com/
def meters_to_miles(meters, sig_figs=2):
    return round(meters * 0.000621371192237333969617434184363, sig_figs)

# XREF: https://www.thecalculatorsite.com/articles/units/meters-in-a-mile.php
def miles_to_meters(miles, sig_figs=2):
    return round(miles * 1609.344, sig_figs)

# Returns a list of fields and the unit of measurement for that field
def fields_list(fnames, sig_figs=2, print_result=False, verbose=False):
    ans = dict()
    counter = 0 
    for fname in fnames:
        with fitdecode.FitReader(fname) as f:
            for frame in f:
                if isinstance(frame, fitdecode.FitDataMessage) and frame.global_mesg_num == 0x14:
                    for field in frame.fields:
                        if field.name not in ans.keys():
                            try:
                                is_custom = field.field_def.is_dev
                            except:
                                is_custom = True
                            if field.name == "timestamp":
                                field.units = 's'
                            try:
                                ans[field.name] = {"units": field.units, "count": 1, "is_custom": is_custom, "def_num": field.field_def.def_num}
                            except AttributeError:
                                ans[field.name] = {"units": field.units, "count": 1, "is_custom": is_custom, "def_num": None}
                        else:
                            ans[field.name]["count"] += 1
                    counter += 1
    for k,v in ans.items():
        v["percentage"] = round(v["count"]/counter * 100, sig_figs)

    # Only if we want to print results directly into console
    if print_result:
        output = list()
        counter = 0
        for k,v in ans.items():
            if v["def_num"]:
                id_val = hex(v["def_num"])
            else:
                id_val = None
            if verbose:
                output.append("Field #{} (ID: {}). '{}' ({}) - appears in {}% of the data [is_custom? {}]".format(counter, id_val, k, v["units"], v["percentage"], v["is_custom"]))
            else:
                output.append("Field #{}. '{}' ({}) - appears in {}% of the data".format(counter, k, v["units"], v["percentage"]))
            counter += 1
        return output
    else:
        return ans   

# Returns dataframe with all yaxes
def gen_dataframes(fnames, force=False):

    log.info("Generating dataframes for {} files".format(len(fnames)))

    yaxes = fields_list(fnames)
    valid_xaxes = ["distance", "timestamp", "rel_time"]

    data = dict()
    for fname in fnames:
        log.debug("Start generating JSON for {}".format(fname))
        start = None
        f_data = { "rel_time": list() }
        for yaxis in yaxes:
            f_data[yaxis] = list()
        with fitdecode.FitReader(fname) as f:
            for frame in f:
                if isinstance(frame, fitdecode.FitDataMessage) and frame.global_mesg_num == 0x14:
                    if start is None:
                        start = frame.get_field("timestamp").raw_value
                    f_data["rel_time"].append(frame.get_field("timestamp").raw_value - start)
                    
                    for yaxis in yaxes:
                        if yaxis == "timestamp":
                            f_data[yaxis].append(frame.get_field(yaxis).raw_value)
                        else:
                            if frame.has_field(yaxis):
                                f_data[yaxis].append(frame.get_field(yaxis).value)
                            else:
                                f_data[yaxis].append(None)
        data[fname] = deepcopy(f_data)
        log.debug("Finished generating JSON for {}".format(fname))

    # Convert dictionaries to dataframes
    log.debug("Converting JSONs to dataframes")
    for fname, d in data.items():
        d = pd.DataFrame(d)
        d["timestamp"] = pd.to_datetime(d["timestamp"], unit='s')
        d = d.add_prefix("{}.".format(fname))
        for valid_xaxis in valid_xaxes:
            d[valid_xaxis] = d["{}.{}".format(fname, valid_xaxis)].copy()
        data[fname] = d

    log.info("Finished generating dataframes")
    return data

def merge_dataframes(xaxis, dfs):
    #result = pd.merge(dfs[0], dfs[1], on=xaxis, how='outer')
    log.debug("Merging dataframes along x-axis: {}".format(xaxis))
    result = reduce(lambda left,right: pd.merge(left, right, on=xaxis, how='outer'), dfs) 
    # Exclude dtypes that aren't numbers
    result = result.select_dtypes(include=["float64", "int64"])
    return result

# TODO
def gen_general_stats():
    pass

def show_dash(dfs_dict):

    app = dash.Dash(__name__)
    yaxes = dict()
    for df in dfs_dict.values():
        for c in list(df.columns):
            tmp = c.split('.')
            if tmp[-1] not in yaxes:
                yaxes[tmp[-1]] = list()
            yaxes[tmp[-1]].append(c)

    #xaxes = ["distance", "timestamp", "rel_time"]
    xaxes = ["distance", "rel_time"]
    loaded_files_markdown = ["### Loaded files:"] + [" * {}".format(_) for _ in list(dfs_dict.keys())]

    app.layout = html.Div(children=[
        dcc.Markdown('\n'.join(loaded_files_markdown)),
        dcc.Checklist(
            id = "yaxes_selection",
            options = [ {"label": x, "value": x} for x in yaxes ],
            value = ["speed"],
            labelStyle={"display": "inline-block"}
        ), 
        dcc.Dropdown(
            id = "xaxis_selection",
            options = [ {"label": x, "value": x} for x in xaxes ],
            value = ["rel_time"]
        ),
        dcc.Graph(id="line-chart")
    ])

    
    @app.callback(
        Output("line-chart", "figure"), 
        [Input("xaxis_selection", "value")],
        [Input("yaxes_selection", "value")],
        # TODO
        # find a way to shift dataset across x or y axis
        #[Input("shift-x", "value")]
    )
    def update_graph(xaxis_selection, yaxes_selection):
        if isinstance(xaxis_selection, list):
            xaxis_selection = xaxis_selection[0]
        mask = [xaxis_selection]
        log.debug("Update graph xaxis: " + str(xaxis_selection))
        log.debug("Update graph yaxis: " + str(yaxes_selection))
        df = merge_dataframes(xaxis_selection, list(dfs_dict.values()))
        for yaxis_selection in yaxes_selection:
            mask += yaxes[yaxis_selection]
        log.debug("Update graph mask: " + str(mask))
        fig = px.line(df[mask], x=xaxis_selection, y=mask)
        fig.update_layout(hovermode='x')
        return fig

    app.run_server(debug=True)
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", help="Forces multiple .fit files into the same plot", action='store_true')
    # TODO
    #parser.add_argument("--config", '-c', help="Configuration file containing extra info such as heart rate zones in yaml format", type=argparse.FileType('r'), default="config.yaml")
    parser.add_argument("--files", help="Space separated list of .fit files to parse through", required=True, nargs="+")
    args = parser.parse_args()

    dfs_dict = gen_dataframes(args.files)

    show_dash(dfs_dict)
