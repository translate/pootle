var webpack = require('webpack');
var join = require('path').join;

var env = process.env.NODE_ENV;
var plugins;


if (env === 'production') {
  plugins = [
    new webpack.DefinePlugin({
      'process.env': {NODE_ENV: JSON.stringify('production')}
    }),
    new webpack.optimize.UglifyJsPlugin()
  ];
} else {
  env = 'development';
  plugins = [
    new webpack.DefinePlugin({
      'process.env': {NODE_ENV: JSON.stringify('development')}
    }),
  ];
}


module.exports = {
  context: __dirname,
  entry: {
    admin: './admin/app.js',
  },
  output: {
    path: __dirname,
    filename: './[name]/app.bundle.js'
  },
  module: {
    loaders: [
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
