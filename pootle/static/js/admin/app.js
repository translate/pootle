/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import 'imports?Backbone=>require("backbone")!backbone-move';

import Backbone from 'backbone';
import React from 'react';

import AdminController from './components/AdminController';
import AdminRouter from './AdminRouter';


window.PTL = window.PTL || {};


const itemTypes = {
  user: require('./components/User'),
  language: require('./components/Language'),
  project: require('./components/Project'),
};


PTL.admin = {

  init(opts) {
    if (!itemTypes.hasOwnProperty(opts.itemType)) {
      throw new Error('Invalid `itemType`.');
    }

    React.render(
      <AdminController
        adminModule={itemTypes[opts.itemType]}
        appRoot={opts.appRoot}
        formChoices={opts.formChoices || {}}
        router={new AdminRouter()}
      />,
      document.querySelector('.js-admin-app')
    );
  }

};
