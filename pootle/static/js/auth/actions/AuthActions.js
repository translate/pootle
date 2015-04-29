/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import { Actions } from 'flummox';

import AuthAPI from '../utils/AuthAPI';


export default class AuthActions extends Actions {

  gotoScreen(screenName) {
    return screenName;
  }

  signIn(reqData, nextURL) {
    return AuthAPI.signIn(reqData, nextURL)
                  .then(
                    (value) => Promise.resolve(value.location),
                    (reason) => Promise.reject(reason.responseJSON.errors)
                  );
  }

  signUp(reqData) {
    return AuthAPI.signUp(reqData)
                  .then(
                    (value) => Promise.resolve(value),
                    (reason) => Promise.reject(reason.responseJSON.errors)
                  );
  }

  requestPasswordReset(reqData) {
    return AuthAPI.requestPasswordReset(reqData)
                  .then(
                    (value) => Promise.resolve(value),
                    (reason) => Promise.reject(reason.responseJSON.errors)
                  );
  }

  passwordReset(reqData, url) {
    // FIXME: ideally we shouldn't be passing in the full URL, but only
    // the necessary bits to construct it
    return AuthAPI.passwordReset(reqData, url)
                  .then(
                    (value) => Promise.resolve(value),
                    (reason) => Promise.reject(reason.responseJSON.errors)
                  );
  }

}
