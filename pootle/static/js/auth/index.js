/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import FluxComponent from 'flummox/component';
import $ from 'jquery';
import assign from 'object-assign';
import React from 'react';


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
    // FIXME: ugly workaround to avoid crashing: some globals
    // (`gettext()`, `l()`) are being used in these modules, so for the
    // time being we delay their import here (note they are CommonJS
    // requires).
    // The actual fix is getting rid of those globals, and only then we'll
    // be able to move these two imports to the top of the module.
    let Flux = require('./flux');
    let AuthController = require('./components/AuthController');

    let flux = new Flux();
    let newProps = assign({}, commonProps, props);

    let AuthApp = (
      <FluxComponent flux={flux} connectToStores={['auth']}>
        <AuthController onClose={this.close} {...newProps} />
      </FluxComponent>
    );

    React.render(AuthApp, document.querySelector(mountNodeSelector));
  },

  close() {
    React.unmountComponentAtNode(document.querySelector(mountNodeSelector));
  },

};
