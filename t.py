#!/usr/bin/python3

import fitdecode
import argparse

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

def gen_dataframe(xaxis, yaxes):
    import pandas as pd
    import plotly.express as px

    assert xaxis in ["relative", "absolute", "distance"]
    if xaxis == "absolute":
        xaxis = "timestamp"
    elif xaxis == "distance":
        xaxis = "distance"
    else:
        xaxis = "time+0"
        start = None

    data = {xaxis: list()}
    for yaxis in yaxes:
        data[yaxis] = list()

    
    

    

# 1. Ask a user which field(s) they want to chart over
"""
Default: speed, heart rate, distance, cadence - required fields as per https://developer.garmin.com/fit/protocol/ (Record 7)
"""
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--xaxis", "-x", help="Use one of: 'absolute', 'relative', or 'distance'.\n'absolute' - use epoch timestamps given by the .fit file as the x-axis\n'relative' - use relative timestamps where your time starts at 0 and every second into the workout is +1 second\n'distance' - use distance as the x-axis\n'Default: 'absolute'", default="absolute")
    parser.add_argument("--list-fields", "-l", help="Lists all the available fields in all files", action='store_true')
    #parser.add_argument("--interactive", help="Interactively choose the options you want to use", action='store_true')
    parser.add_argument("--fields", "--yaxis", "-y", help="The fields within the .fit files you wish you chart over") 
    parser.add_argument("--files", help="Space separated list of .fit files to parse through", required=True, nargs="+")
    args = parser.parse_args()

    if args.list_fields:
        ret = fields_list(args.files, print_result=True)
        for _ in ret:
            print(_)
        exit(0)

    fit1 = "Run20210721072634.fit"
    fit2 = "Run20210727072255.fit"

    limit = 1000000
    counter = 0
    start_epoch = None

    data = {"timestamp": list(), "speed": list()}

    with fitdecode.FitReader(fit1) as f:
        for frame in f:
            if counter < limit:
                if isinstance(frame, fitdecode.FitDataMessage):
                    if frame.global_mesg_num == 0x14:
                        data["timestamp"].append(frame.get_field("timestamp").raw_value)
                        if frame.has_field("speed"):
                            _ = frame.get_field("speed").value
                            if _:
                                data["speed"].append(_)
                            else:
                                data["speed"].append(0)
                        else:
                            data["speed"].append(0)

                counter += 1
            else:
                break

    df = pd.DataFrame(data=data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit='s')
    
    fig = px.line(df, x="timestamp", y="speed")
    fig.show()
    
