/*
 * Copyright 2012, Serge V. Izmaylov
 * Released under GPL Version 2 license.
 */

/*
Flot plugin for rendering x-axis marks on plot canvas.
Plugin assumes mark positions given in primary x-axis scale.

* Created by Serge V. Izmaylov Mar 2012

Available options are:
series: {
    marks: {
        show: true/false -- enable plugin for given data series,
        lineWidth: -- thickness of mark outline
        toothSize: -- height of top & bottom trinangle marks
        color: -- mark outline color
        fill: true/false -- trinagle marks may be filled with color
        fillColor: -- color for filling interior of triangle mark
        showLabels: -- marks may be labeled,
        rowHeight: -- mark labels are aligned on several rows with that height
        rows: -- how many label rows used
        labelVAlign: "top"/"bottom" -- label rows may lay on the floor or hang from the ceiling
        labelHAlign: "left"/"right" -- labels may be aligned to left or right side of mark
    }
}

Marks are defined in series.markdata:
series {
    marks: { show: true, <here goes mark set specific options> }
    extentdata: [ {
        label: -- (optional) text label for mark
        id: -- (optional) html ID attribute value for label's DIV
        position: -- (mandatory) x coordinate of mark
        labelHAlign: -- (optional) change vertical label alignment for that mark only
        labelVAlign: -- (optional) change horizontal label alignment for that mark only
        row: -- (optional) force label of that mark to lay in given row
    }, ... ]
}

See samples.html & source below. Feel free to extend the marks.

*/

(function ($) {
    var options = {
        series: {
            marks: {
                show: false,
                lineWidth: 1,
                toothSize: 9,
                color: "rgba(128, 128, 128, 1.0)",
                fill: true,
                fillColor: "rgba(64, 128, 192, 0.6)",
                showLabels: true,
                rowHeight: 20,
                rows: 2,
                labelVAlign: "bottom",
                labelHAlign: "right"
            }
        }
    };

    function processRawData(plot, series, data, datapoints) {
        if (!series.marks || !series.marks.show)
            return;

        // Fool Flot with fake datapoints
        datapoints.format = [ // Fake format
            { x: true, number: true, required: true },
            { y: true, number: true, required: true },
        ];
        datapoints.points = []; // Empty data
        datapoints.pointsize = 2; // Fake size

        // Process our real data
        if (series.markdata == null)
            series.markdata = [];
        var row = 0;
        for (i = 0; i<series.markdata.length; i++) {
            if (series.markdata[i].position == null)
                series.markdata[i].position = 0.0;
            if ((series.markdata[i].labelVAlign != "top") && (series.markdata[i].labelVAlign != "bottom"))
                series.markdata[i].labelVAlign = series.marks.labelVAlign;
            if ((series.markdata[i].labelHAlign != "left") && (series.markdata[i].labelHAlign != "right"))
                series.markdata[i].labelHAlign = series.marks.labelHAlign;
            if (series.markdata[i].row == null) {
                series.markdata[i].row = row;
                row = (row+1) % series.marks.rows;
            } else {
                row = (series.markdata[i].row+1) % series.marks.rows;
            }
        }
    };

    function drawSingleMark(ctx, x, ytop, ybot, w2, h2, series) {

        ctx.beginPath();

        ctx.moveTo(x, ytop+h2);
        ctx.lineTo(x-w2, ytop-h2);
        ctx.lineTo(x+w2, ytop-h2);
        ctx.lineTo(x, ytop+h2);

        ctx.lineTo(x, ybot-h2);
        ctx.lineTo(x+w2, ybot+h2);
        ctx.lineTo(x-w2, ybot+h2);
        ctx.lineTo(x, ybot-h2);
        ctx.lineTo(x, ytop+h2);


        ctx.stroke();
        if (series.marks.fill) ctx.fill();
    }

    function addMarkLabel(placeholder, plotOffset, width, x, row, series, label, hAlign, vAlign, id) {
        var styles = [];
        if (vAlign == "top")
            styles.push("top:"+Math.round((plotOffset.top+series.marks.rowHeight*row+4))+"px");
        else
            styles.push("bottom:"+Math.round((plotOffset.bottom+series.marks.rowHeight*row+4))+"px");
        if (hAlign == "left")
            styles.push("right:"+Math.round((plotOffset.right+width-x+3))+"px");
        else
            styles.push("left:"+Math.round((plotOffset.left+x+3))+"px");
        styles.push("");

        placeholder.append('<div '+((id !=null)?('id="'+id+'" '):'')+'class="markLabel" style="font-size:smaller;position:absolute;'+(styles.join(';'))+'">'+label+'</div>');
    }

    function drawSeries(plot, ctx, series) {
        if (!series.marks || !series.marks.show)
            return;

        var placeholder = plot.getPlaceholder();
        placeholder.find(".markLabel").remove();

        ctx.save();

        var plotOffset = plot.getPlotOffset();
        var axes = plot.getAxes();
        var yf = axes.yaxis.p2c(axes.yaxis.min);
        var yt = axes.yaxis.p2c(axes.yaxis.max);
        var ytop = (yf>yt)?yt:yf;
        var ybot = (yf>yt)?yf:yt;
        var h2 = Math.floor((series.marks.toothSize+1)/2);
        var w2 = Math.floor(series.marks.toothSize*.4);

        ctx.translate(plotOffset.left, plotOffset.top);
        ctx.lineJoin = "round";
        ctx.lineWidth = series.marks.lineWidth;
        ctx.strokeStyle = series.marks.color;
        ctx.fillStyle = series.marks.fillColor;

        for (var i = 0; i < series.markdata.length; i++)
            if ((series.markdata[i].position >= axes.xaxis.min) && (series.markdata[i].position <= axes.xaxis.max)) {
              var x = axes.xaxis.p2c(series.markdata[i].position);
              drawSingleMark(ctx, x, ytop, ybot, w2, h2, series);
            }

        ctx.restore();

        if (series.marks.showLabels)
            for (var i = 0; i < series.markdata.length; i++)
                if ((series.markdata[i].position >= axes.xaxis.min) && (series.markdata[i].position <= axes.xaxis.max) && (series.markdata[i].label != null)) {
                    var x = axes.xaxis.p2c(series.markdata[i].position);
                    addMarkLabel(placeholder, plotOffset, plot.width(), x, series.markdata[i].row, series, series.markdata[i].label, series.markdata[i].labelHAlign, series.markdata[i].labelVAlign, series.markdata[i].id);
                }
    };

    function init(plot) {
        plot.hooks.processRawData.push(processRawData);
        plot.hooks.drawSeries.push(drawSeries);
    };

    $.plot.plugins.push({
        init: init,
        name: "marks",
        options: options,
        version: "0.1"
    });
})(jQuery);
