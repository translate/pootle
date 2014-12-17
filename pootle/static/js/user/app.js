'use strict';

var React = require('react/addons');

var User = require('../models/user').User;
var UserProfileEdit = require('./components/edit');
var UserProfileRouter = require('./routers');


window.PTL = window.PTL || {};


PTL.user = {

  init: function (opts) {
    this.el = document.querySelector(opts.el);

    var user = new User(opts.userData, {urlRoot: l('/xhr/users/')});
    var userProfileEdit = new UserProfileEdit({
      router: new UserProfileRouter(),
      appRoot: opts.appRoot,
      user: user
    });
    React.renderComponent(userProfileEdit, this.el);
  }

};
