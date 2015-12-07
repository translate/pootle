/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import fetch from 'utils/fetch';


const AuthAPI = {

  apiRoot: '/accounts/',

  fetch(url, body) {
    return fetch({ url, body, method: 'POST' });
  },

  signIn(reqData, nextURL) {
    const url = `${this.apiRoot}login/?next=${encodeURIComponent(nextURL)}`;

    return this.fetch(url, reqData);
  },

  signUp(reqData) {
    const url = `${this.apiRoot}signup/`;

    return this.fetch(url, reqData);
  },

  requestPasswordReset(reqData) {
    const url = `${this.apiRoot}password/reset/`;

    return this.fetch(url, reqData);
  },

  passwordReset(reqData, reqUrl) {
    let url = reqUrl;
    // XXX: this won't work still as we don't have the data separately
    if (!url) {
      const { uidb36, key } = reqData;
      url = `${this.apiRoot}password/reset/key/${uidb36}-${key}/`;
    }

    return this.fetch(url, reqData);
  },

  verifySocial(reqData) {
    const url = `${this.apiRoot}social/verify/`;

    return this.fetch(url, reqData);
  },

};


export default AuthAPI;
