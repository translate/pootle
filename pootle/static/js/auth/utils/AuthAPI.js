/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import $ from 'jquery';


const AuthAPI = {

  apiRoot: l('/accounts/'),

  request(url, data) {
    return Promise.resolve(
      $.ajax(url, {
        type: 'POST',
        data: data,
        dataType: 'json',
      })
    );
  },

  signIn(reqData, nextURL) {
    const url = `${this.apiRoot}login/?next=${encodeURIComponent(nextURL)}`;

    return this.request(url, reqData);
  },

  signUp(reqData) {
    const url = `${this.apiRoot}signup/`;

    return this.request(url, reqData);
  },

  requestPasswordReset(reqData) {
    const url = `${this.apiRoot}password/reset/`;

    return this.request(url, reqData);
  },

  passwordReset(reqData, url) {
    // XXX: this won't work still as we don't have the data separately
    if (!url) {
      const { uidb36, key } = reqData;
      url = `${this.apiRoot}password/reset/key/${uidb36}-${key}/`;
    }

    return this.request(url, reqData);
  },

  verifySocial(reqData) {
    const url = `${this.apiRoot}social/verify/`;

    return this.request(url, reqData);
  },

};


export default AuthAPI;
