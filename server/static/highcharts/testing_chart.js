Highcharts.stockChart('container', {
    series: [{
        type: 'ohlc',
            data: {{ kraken_data }}
        }]
    });