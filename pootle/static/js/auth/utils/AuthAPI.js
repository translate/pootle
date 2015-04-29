/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import $ from 'jquery';


let AuthAPI = {

  apiRoot: l('/accounts/'),

  signIn(reqData, nextURL) {
    let url = `${this.apiRoot}login/?next=${encodeURIComponent(nextURL)}`;

    return Promise.resolve(
      $.ajax(url, {
        type: 'POST',
        data: reqData,
        dataType: 'json',
      })
    );
  },

  signUp(reqData) {
    let url = `${this.apiRoot}signup/`;

    return Promise.resolve(
      $.ajax(url, {
        type: 'POST',
        data: reqData,
        dataType: 'json',
      })
    );
  },

  requestPasswordReset(reqData) {
    let url = `${this.apiRoot}password/reset/`;

    return Promise.resolve(
      $.ajax(url, {
        type: 'POST',
        data: reqData,
        dataType: 'json',
      })
    );
  },

  passwordReset(reqData, url) {
    // XXX: this won't work still as we don't have the data separately
    if (!url) {
      let { uidb36, key } = reqData;
      url = `${this.apiRoot}password/reset/key/${uidb36}-${key}/`;
    }

    return Promise.resolve(
      $.ajax(url, {
        type: 'POST',
        data: reqData,
        dataType: 'json',
      })
    );
  },

};


export default AuthAPI;
