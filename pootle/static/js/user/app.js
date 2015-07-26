/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

var React = require('react');

var User = require('models/user').User;
var UserProfileEditClass = require('./components/edit');
var UserProfileRouter = require('./routers');

var UserProfileEdit = React.createFactory(UserProfileEditClass);


window.PTL = window.PTL || {};


PTL.user = {

  init: function (opts) {
    const el = document.querySelector(opts.el);

    var user = new User(opts.userData, {urlRoot: l('/xhr/users/')});
    var userProfileEdit = new UserProfileEdit({
      router: new UserProfileRouter(),
      appRoot: opts.appRoot,
      user: user
    });
    React.render(userProfileEdit, el);
  }

};
