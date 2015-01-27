'use strict';

var React = require('react');

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
  language: require('./components/language'),
  project: require('./components/project'),
};


PTL.admin = {

  init: function (opts) {
    var el = document.querySelector(opts.el || '.js-admin-app');

    if (!itemTypes.hasOwnProperty(opts.itemType)) {
      throw new Error('Invalid `itemType`.');
    }

    var item = itemTypes[opts.itemType];
    var main = new AdminApp({
      router: new AdminRouter(),
      appRoot: opts.appRoot,
      adminModule: item,
      formChoices: opts.formChoices || {},
    });
    React.render(main, el);
  }

};
