/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

var webpack = require('webpack');
var path = require('path');
var _ = require('lodash');

var env = process.env.NODE_ENV;
var DEBUG = env !== 'production';


var entries = {
  'admin/general': './admin/general/app.js',
  admin: './admin/app.js',
  user: './user/app.js',
  common: ['./common.js'],
  editor: ['./editor/app.js'],
  reports: ['./reports/app.js'],
  vendor: ['react', 'react/addons', 'jquery', 'underscore', 'backbone'],
};


var resolve = {
  extensions: ['', '.js', '.jsx'],
  modulesDirectories: ['node_modules', 'shared'],
  alias: {
    pootle: __dirname,

    jquery: __dirname + '/vendor/jquery/jquery.js',
    backbone: __dirname + '/vendor/backbone/backbone.js',
    underscore: __dirname + '/vendor/underscore.js',

    'backbone-move': __dirname + '/vendor/backbone/backbone.move.js',
    'backbone-safesync': __dirname + '/vendor/backbone/backbone.safesync.js',
    // FIXME: get rid of bb-router
    'backbone-queryparams': __dirname + '/vendor/backbone/backbone.queryparams.js',
    'backbone-queryparams-shim': __dirname + '/vendor/backbone/backbone.queryparams-1.1-shim.js',
    'backbone-relational': __dirname + '/vendor/backbone/backbone-relational.js',

    'jquery-autosize': __dirname + '/vendor/jquery/jquery.autosize.js',
    'jquery-bidi': __dirname + '/vendor/jquery/jquery.bidi.js',
    'jquery-caret': __dirname + '/vendor/jquery/jquery.caret.js',
    'jquery-cookie': __dirname + '/vendor/jquery/jquery.cookie.js',
    'jquery-easing': __dirname + '/vendor/jquery/jquery.easing.js',
    'jquery-flot': __dirname + '/vendor/jquery/jquery.flot.js',
    'jquery-flot-stack': __dirname + '/vendor/jquery/jquery.flot.stack.js',
    'jquery-flot-marks': __dirname + '/vendor/jquery/jquery.flot.marks.js',
    'jquery-flot-time': __dirname + '/vendor/jquery/jquery.flot.time.js',
    'jquery-highlightRegex': __dirname + '/vendor/jquery/jquery.highlightRegex.js',
    'jquery-history': __dirname + '/vendor/jquery/jquery.history.js',
    'jquery-jsonp': __dirname + '/vendor/jquery/jquery.jsonp.js',
    'jquery-magnific-popup': __dirname + '/vendor/jquery/jquery.magnific-popup.js',
    'jquery-select2': __dirname + '/vendor/jquery/jquery.select2.js',
    'jquery-serializeObject': __dirname + '/vendor/jquery/jquery.serializeObject.js',
    'jquery-tipsy': __dirname + '/vendor/jquery/jquery.tipsy.js',
    'jquery-utils': __dirname + '/vendor/jquery/jquery.utils.js',

    'bootstrap-alert': __dirname + '/vendor/bootstrap/bootstrap-alert.js',
    'bootstrap-transition': __dirname + '/vendor/bootstrap/bootstrap-transition.js',

    'diff-match-patch': __dirname + '/vendor/diff_match_patch.js', // FIXME: use npm module
    iso8601: __dirname + '/vendor/iso8601.js', // FIXME: use npm module
    levenshtein: __dirname + '/vendor/levenshtein.js', // FIXME: use npm module
    moment: __dirname + '/vendor/moment.js', // FIXME: use npm module
    odometer: __dirname + '/vendor/odometer.js', // FIXME: use npm module
    shortcut: __dirname + '/vendor/shortcut.js',
    sorttable: __dirname + '/vendor/sorttable.js',
    spin: __dirname + '/vendor/spin.js', // FIXME: use npm module
  }
};


// Read extra `resolve.root` paths from the `WEBPACK_ROOT` envvar
// and merge the entry definitions from the manifest files
var root = process.env.WEBPACK_ROOT;
if (root !== undefined) {
  resolve.root = root.split(':');

  var i, customPath, manifestEntries;

  var mergeArrays = function (a, b) {
    return _.isArray(a) ? a.concat(b) : undefined;
  };

  for (i=0; i<resolve.root.length; i++) {
    customPath = resolve.root[i];

    try {
      manifestEntries = require(path.join(customPath, 'manifest.json'));
      entries = _.merge(entries, manifestEntries, mergeArrays);
    } catch (e) {
      console.error(e.message);
    }
  }
}


/* Plugins */

var plugins = [];

if (!DEBUG) {
  plugins = [
    new webpack.optimize.UglifyJsPlugin({
      compress: { warnings: false },
      sourceMap: false,
    }),
    new webpack.optimize.OccurenceOrderPlugin(),
  ];
} else {
  env = 'development';
}

plugins.push.apply(plugins, [
  new webpack.DefinePlugin({
    'process.env': {NODE_ENV: JSON.stringify(env)}
  }),
  new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),
  new webpack.ProvidePlugin({
    'window.Backbone': 'backbone',
  }),
  new webpack.optimize.CommonsChunkPlugin('vendor', 'vendor.bundle.js')
]);


/* Exported configuration */

var config = {
  context: __dirname,
  entry: entries,
  output: {
    path: __dirname,
    filename: './[name]/app.bundle.js'
  },
  module: {
    loaders: [
      { test: /\.css/, loader: 'style-loader!css-loader', exclude: /node_modules/ },
      { test: /\.jsx?$/, loader: 'babel-loader', exclude: /node_modules|vendor/}
    ]
  },
  resolve: resolve,
  plugins: plugins,
};


if (DEBUG) {
  config.debug = true;
  config.devtool = '#source-map';
  config.output.pathinfo = true;
}


module.exports = config;
