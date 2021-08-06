// XREF: https://community.plotly.com/t/programmatically-trigger-hover-events-with-dash/42443

if (!window.dash_clientside) {
    window.dash_clientside = {};
}
window.dash_clientside.clientside = {
    trigger_map_to_metrics_hover: function(hoverData) {
        var myPlot = document.getElementById("metrics_graph")
        if (!myPlot.children[1]) {
            return window.dash_clientside.no_update
        }
        myPlot.children[1].id = "metrics_graph_js"

        if (hoverData) {
            if (Array.isArray(hoverData.points[0].customdata)) {
                var t = hoverData.points[0].customdata[0]
            } else {
                var t = hoverData.points[0].customdata
            }
            t = Math.round(t*10)/10
            Plotly.Fx.hover("metrics_graph_js", {xval: t, yval:0})
        }
        return window.dash_clientside.no_update
    }
}

/*
window.dash_clientside.clientside = {
    trigger_metrics_to_map_hover: function(hoverData) {
        var myPlot = document.getElementById("mapbox")
        if (!myPlot.children[1]) {
            return window.dash_clientside.no_update
        }
        myPlot.children[1].id = "mapbox_js"

        if (hoverData) {
            if (Array.isArray(hoverData.points[0].x)) {
                var t = hoverData.points[0].x[0]
            } else {
                var t = hoverData.points[0].x
            }
            t = Math.round(t*10)/10
            Plotly.Fx.hover("mapbox_js", {xval: t, yval:0})
        }
        return window.dash_clientside.no_update
        
    }    
}
*/
