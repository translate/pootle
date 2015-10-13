/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import fetch from 'utils/xhr';


const AuthAPI = {

  apiRoot: '/accounts/',

  signIn(reqData, nextURL) {
    const url = `${this.apiRoot}login/?next=${encodeURIComponent(nextURL)}`;

    return fetch({ url, body: reqData });
  },

  signUp(reqData) {
    const url = `${this.apiRoot}signup/`;

    return fetch({ url, body: reqData });
  },

  requestPasswordReset(reqData) {
    const url = `${this.apiRoot}password/reset/`;

    return fetch({ url, body: reqData });
  },

  passwordReset(reqData, url) {
    // XXX: this won't work still as we don't have the data separately
    if (!url) {
      const { uidb36, key } = reqData;
      url = `${this.apiRoot}password/reset/key/${uidb36}-${key}/`;
    }

    return fetch({ url, body: reqData });
  },

  verifySocial(reqData) {
    const url = `${this.apiRoot}social/verify/`;

    return fetch({ url, body: reqData });
  },

};


export default AuthAPI;
