var webpack = require('webpack');

var env = process.env.NODE_ENV;
var plugins;


/* Plugins */

if (env === 'production') {
  plugins = [
    new webpack.DefinePlugin({
      'process.env': {NODE_ENV: JSON.stringify('production')}
    }),
    new webpack.optimize.UglifyJsPlugin(),
  ];
} else {
  env = 'development';
  plugins = [
    new webpack.DefinePlugin({
      'process.env': {NODE_ENV: JSON.stringify('development')}
    }),
  ];
}

plugins.push.apply(plugins, [
  new webpack.optimize.CommonsChunkPlugin('vendor', 'vendor.bundle.js')
]);


/* Exported configuration */

module.exports = {
  context: __dirname,
  entry: {
    admin: './admin/app.js',
    user: './user/app.js',
    vendor: ['react', 'jquery', 'underscore', 'backbone'],
  },
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
  resolve: {
    extensions: ['', '.js', '.jsx']
  },
  plugins: plugins,
  externals: {
    // avoid duplicating external scripts already available on the global scope
    backbone: 'Backbone',
    jquery: 'jQuery',
    underscore: '_'
  }
};
