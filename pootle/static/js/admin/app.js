'use strict';

var React = require('react/addons');

var Backbone = require('backbone');

require('backbone-queryparams');
require('backbone-queryparams-shim');
require('imports?Backbone=>require("backbone")!backbone-move');

var AdminAppClass = require('./components/main');
var AdminRouter = require('./routers');

var AdminApp = React.createFactory(AdminAppClass);


window.PTL = window.PTL || {};


var itemTypes = {
  user: require('./components/user'),
};


PTL.admin = {

  init: function (opts) {
    this.el = document.querySelector(opts.el);

    if (!itemTypes.hasOwnProperty(opts.itemType)) {
      throw new Error('Invalid `itemType`.');
    }

    var item = itemTypes[opts.itemType];
    var main = new AdminApp({
      router: new AdminRouter(),
      appRoot: opts.appRoot,
      adminModule: item,
    });
    React.render(main, this.el);
  }

};
