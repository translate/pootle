var webpack = require('webpack');
var path = require('path');
var _ = require('lodash');

var env = process.env.NODE_ENV;


var entries = {
  admin: './admin/app.js',
  user: './user/app.js',
  vendor: ['react', 'jquery', 'underscore', 'backbone'],
};


var resolve = {
  extensions: ['', '.js', '.jsx'],
  alias: {
    pootle: __dirname,
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

if (env === 'production') {
  plugins = [
    new webpack.optimize.UglifyJsPlugin(),
  ];
} else {
  env = 'development';
}

plugins.push.apply(plugins, [
  new webpack.DefinePlugin({
    'process.env': {NODE_ENV: JSON.stringify(env)}
  }),
  new webpack.optimize.CommonsChunkPlugin('vendor', 'vendor.bundle.js')
]);


/* Exported configuration */

module.exports = {
  context: __dirname,
  entry: entries,
  output: {
    path: __dirname,
    filename: './[name]/app.bundle.js'
  },
  module: {
    loaders: [
      { test: /\.css/, loader: "style-loader!css-loader" },
      { test: /\.jsx$/, loader: 'jsx-loader?harmony&insertPragma=React.DOM' },
    ]
  },
  resolve: resolve,
  plugins: plugins,
  externals: {
    // FIXME: ideally everything should be using CommonJS modules now, and
    // this shouldn't be necessary at all.
    // Avoid duplicating external scripts available on the global scope
    backbone: 'Backbone',
    jquery: 'jQuery',
    underscore: '_'
  }
};
