
var path=require('path');
var webpack = require('webpack');
var nodeExternals = require('webpack-node-externals');

const config = {
  target:'node',
  entry: {
    main: './index.js'
  },
  output: {
    filename: '[name].bin.js',
    // Output path using nodeJs path module
    path: path.resolve(__dirname, '.')
  },
  externals: [nodeExternals()],
  plugins: [
    new webpack.IgnorePlugin(/vertx/)
  ],
  module: {
    rules: [
      {
        test: /node_modules[/\\]mqtt/i,
        ///node_modules\/mqtt\/mqtt\.js$/,
        use: [{
          loader: 'shebang-loader'
        }]
      }
    ]
  }
};
module.exports = config;
