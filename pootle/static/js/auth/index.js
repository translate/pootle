/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import $ from 'jquery';
import assign from 'object-assign';
import React from 'react';
import { Provider } from 'react-redux';
import { createStore } from 'redux';

import AuthController from './components/AuthController';
import authReducer from './reducers';


const mountNodeSelector = '.js-auth';
const commonProps = {
  canContact: PTL.settings.CONTACT_ENABLED,
  canRegister: PTL.settings.SIGNUP_ENABLED,
  socialAuthProviders: PTL.settings.SOCIAL_AUTH_PROVIDERS,
};


module.exports = {

  init(props) {
    $(document).on('click', '.js-login', (e) => {
      e.preventDefault();

      this.open(props);
    });
  },

  open(props) {
    const newProps = assign({}, commonProps, props);

    let store = createStore(authReducer);

    React.render(
      <Provider store={store}>
        {() => <AuthController onClose={this.close} {...newProps} />}
      </Provider>,
      document.querySelector(mountNodeSelector)
    );
  },

  close() {
    React.unmountComponentAtNode(document.querySelector(mountNodeSelector));
  },

};
