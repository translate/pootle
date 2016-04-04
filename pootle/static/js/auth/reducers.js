/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import { combineReducers } from 'redux';


function screen(state = 'signIn', action) {
  switch (action.type) {
    case 'GOTO_SCREEN':
      return action.screen;

    case 'SIGNIN_SUCCESS': {
      const { nextURL } = action;
      // HACKISH: allauth's XHR responses are not very informative, so
      // it's necessary to do some guesswork around URLs in order to know
      // what the actual response is supposed to mean
      if (nextURL.indexOf('confirm-email') !== -1) {
        return 'activation';
      } else if (nextURL.indexOf('inactive') !== -1) {
        return 'inactive';
      }
      return state;
    }

    case 'SIGNUP_SUCCESS':
      return 'activation';

    case 'REQ_PW_RESET_SUCCESS':
      return 'requestPasswordResetSent';

    default:
      return state;
  }
}


function isLoading(state = false, action) {
  switch (action.type) {
    case 'SIGNIN_REQUEST':
    case 'SIGNUP_REQUEST':
    case 'REQ_PW_RESET_REQUEST':
    case 'PW_RESET_REQUEST':
    case 'VERIFY_SOCIAL_REQUEST':
      return true;

    case 'SIGNIN_SUCCESS':
    case 'SIGNIN_FAILURE':
    case 'SIGNUP_SUCCESS':
    case 'SIGNUP_FAILURE':
    case 'REQ_PW_RESET_SUCCESS':
    case 'REQ_PW_RESET_FAILURE':
    case 'PW_RESET_SUCCESS':
    case 'PW_RESET_FAILURE':
    case 'VERIFY_SOCIAL_SUCCESS':
    case 'VERIFY_SOCIAL_FAILURE':
      return false;

    default:
      return state;
  }
}


function redirectTo(state = null, action) {
  switch (action.type) {
    case 'SIGNIN_SUCCESS': {
      const { nextURL } = action;
      if (nextURL.indexOf('confirm-email') !== -1 ||
            nextURL.indexOf('inactive') !== -1) {
        return state;
      }
      return nextURL;
    }

    case 'PW_RESET_SUCCESS':
        // FIXME: hard-coding redirect path because of django-allauth#735
      return l('/');

    case 'VERIFY_SOCIAL_SUCCESS':
      return action.nextURL;

    default:
      return state;
  }
}


function resetEmail(state = null, action) {
  switch (action.type) {
    case 'REQ_PW_RESET_REQUEST':
      return action.email;

    default:
      return state;
  }
}


function signUpEmail(state = null, action) {
  switch (action.type) {
    case 'SIGNUP_REQUEST':
      return action.email;

    default:
      return state;
  }
}


function formErrors(state = {}, action) {
  switch (action.type) {
    case 'SIGNIN_FAILURE':
    case 'SIGNUP_FAILURE':
    case 'REQ_PW_RESET_FAILURE':
    case 'PW_RESET_FAILURE':
    case 'VERIFY_SOCIAL_FAILURE':
      return action.errors;

    case 'SIGNIN_REQUEST':
    case 'SIGNIN_SUCCESS':
    case 'SIGNUP_REQUEST':
    case 'SIGNUP_SUCCESS':
    case 'REQ_PW_RESET_REQUEST':
    case 'REQ_PW_RESET_SUCCESS':
    case 'PW_RESET_REQUEST':
    case 'PW_RESET_SUCCESS':
    case 'VERIFY_SOCIAL_REQUEST':
    case 'VERIFY_SOCIAL_SUCCESS':
      return {};

    default:
      return state;
  }
}


const authReducer = combineReducers({
  screen,
  redirectTo,
  resetEmail,
  signUpEmail,
  isLoading,
  formErrors,
});


export default authReducer;
