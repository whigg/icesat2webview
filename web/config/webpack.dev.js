const paths = require('./paths')
const path = require('path')
const webpack = require('webpack')
const { merge } = require('webpack-merge')
const common = require('./webpack.common.js')

module.exports = merge(common, {
  // Set the mode to development or production
  mode: 'development',

  // Control how source maps are generated
  devtool: 'inline-source-map',

  // Spin up a server for quick development
  devServer: {
    //historyApiFallback: true,
   // contentBase: [ path.join(__dirname,"tiles")],
    publicPath: "/",
    https:true,
    open: false,
    compress: true,
    hot: true,
    port: 8443,
    serveIndex:true,

    contentBase: [ path.join(__dirname+"/..", 'tiles')],
    contentBasePublicPath: [ '/tiles'],
  },

  plugins: [
    // Only update what has changed on hot reload
    new webpack.HotModuleReplacementPlugin(),
  ],
})
