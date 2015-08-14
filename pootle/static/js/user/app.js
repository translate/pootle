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
var UserProfileRouter = require('./routers');

import UserProfileEdit from './components/UserProfileEdit';


window.PTL = window.PTL || {};


PTL.user = {

  init: function (opts) {
    const el = document.querySelector(opts.el);

    var user = new User(opts.userData, {urlRoot: l('/xhr/users/')});
    const props = {
      router: new UserProfileRouter(),
      appRoot: opts.appRoot,
      user: user
    };
    React.render(<UserProfileEdit {...props} />, el);

    // FIXME: let's make the whole profile page a component, so a lot of the
    // boilerplate here is rendered redundant
    const popupBtns = document.querySelectorAll('.js-popup-tweet');
    [...popupBtns].map((btn) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();

        const width = 500;
        const height = 260;
        const left = (screen.width / 2) - (width / 2);
        const top = (screen.height / 2) - (height / 2);
        window.open(e.currentTarget.href, '_blank',
                    `width=${width},height=${height},left=${left},top=${top}`);
      });
    });
  }

};
