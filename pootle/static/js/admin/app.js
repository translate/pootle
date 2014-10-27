'use strict';

var React = require('react/addons');

var Backbone = require('backbone');

require('backbone-queryparams');
require('backbone-queryparams-shim');
require('imports?Backbone=>require("backbone")!backbone-move');

var AdminApp = require('./components/main');
var AdminRouter = require('./routers');


window.PTL = window.PTL || {};


var itemTypes = {
  user: {
    model: require('../models/user').User,
    collection: require('../models/user').UserSet
  }
};


PTL.admin = {

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
