/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';


import 'backbone-queryparams';
import 'backbone-queryparams-shim';
import 'imports?Backbone=>require("backbone")!backbone-move';

import Backbone from 'backbone';
import React from 'react';

import AdminController from './components/AdminController';
import AdminRouter from './routers';

let AdminApp = React.createFactory(AdminController);


window.PTL = window.PTL || {};


const itemTypes = {
  user: require('./components/user'),
  language: require('./components/language'),
  project: require('./components/project'),
};


PTL.admin = {

  init(opts) {
    let el = document.querySelector(opts.el || '.js-admin-app');

    if (!itemTypes.hasOwnProperty(opts.itemType)) {
      throw new Error('Invalid `itemType`.');
    }

    let item = itemTypes[opts.itemType];
    let main = new AdminApp({
      router: new AdminRouter(),
      appRoot: opts.appRoot,
      adminModule: item,
      formChoices: opts.formChoices || {},
    });
    React.render(main, el);
  }

};
