'use strict';

// External deps
// TODO: get rid of BB router; this shouldn't be necessary at all
require('imports!../vendor/backbone/backbone.queryparams.js');
require('imports!../vendor/backbone/backbone.queryparams-1.1-shim.js');
require('imports!../vendor/backbone/backbone.move.js');

var React = require('react/addons');

var AdminApp = require('./components/main');
var AdminRouter = require('./routers');


window.PTL = window.PTL || {};


PTL.admin = (function () {

  var itemTypes = {
    user: {
      model: require('../models/user').User,
      collection: require('../models/user').UserSet
    }
  };

  return {

    init: function (opts) {
      this.el = document.querySelector(opts.el);

      if (!opts.itemType in itemTypes) {
        throw new Error('Invalid `itemType`.');
      }

      var item = itemTypes[opts.itemType];
      var main = new AdminApp({
        router: new AdminRouter(),
        appRoot: opts.appRoot,
        collection: item.collection,
        model: item.model
      });
      React.renderComponent(main, this.el);
    }

  };

}());
