/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import AuthAPI from './utils/AuthAPI';


export const GOTO_SCREEN = 'GOTO_SCREEN';


export function gotoScreen(screen) {
  return {
    type: GOTO_SCREEN,
    screen: screen,
  };
}


/**
 * Takes care of creating an object which contains errors related to
 * authentication and unhandled exceptions.
 */
function handleErrors(jsonResponse={}) {
  let errors = {};

  if ('errors' in jsonResponse) {
    errors = jsonResponse.errors;
  }
  if ('msg' in jsonResponse) {
    errors = {
      '__all__': [jsonResponse.msg],
    };
  }

  return errors;
}


export const SIGNIN_REQUEST = 'SIGNIN_REQUEST';
export const SIGNIN_SUCCESS = 'SIGNIN_SUCCESS';
export const SIGNIN_FAILURE = 'SIGNIN_FAILURE';


export function signIn(formData, nextURL) {
  return dispatch => {
    dispatch(signInRequest());

    return AuthAPI.signIn(formData, nextURL)
                  .then(
                    (data) => dispatch(signInSuccess(data.location)),
                    (data) => dispatch(signInFailure(data.responseJSON))
                  );
  }
}


function signInRequest() {
  return {
    type: SIGNIN_REQUEST,
  }
}


function signInSuccess(nextURL) {
  return {
    type: SIGNIN_SUCCESS,
    nextURL,
  }
}


function signInFailure(jsonResponse) {
  return {
    type: SIGNIN_FAILURE,
    errors: handleErrors(jsonResponse),
  }
}


export const SIGNUP_REQUEST = 'SIGNUP_REQUEST';
export const SIGNUP_SUCCESS = 'SIGNUP_SUCCESS';
export const SIGNUP_FAILURE = 'SIGNUP_FAILURE';


export function signUp(formData, nextURL) {
  return dispatch => {
    dispatch(signUpRequest(formData.email));

    return AuthAPI.signUp(formData, nextURL)
                  .then(
                    (data) => dispatch(signUpSuccess(data.location)),
                    (data) => dispatch(signUpFailure(data.responseJSON))
                  );
  }
}


function signUpRequest(email, nextURL) {
  return {
    type: SIGNUP_REQUEST,
    email,
  }
}


function signUpSuccess(nextURL) {
  return {
    type: SIGNUP_SUCCESS,
    nextURL,
  }
}


function signUpFailure(jsonResponse) {
  return {
    type: SIGNUP_FAILURE,
    errors: handleErrors(jsonResponse),
  }
}


export const REQ_PW_RESET_REQUEST = 'REQ_PW_RESET_REQUEST';
export const REQ_PW_RESET_SUCCESS = 'REQ_PW_RESET_SUCCESS';
export const REQ_PW_RESET_FAILURE = 'REQ_PW_RESET_FAILURE';


export function requestPasswordReset(formData) {
  return dispatch => {
    dispatch(requestPasswordResetRequest(formData.email));

    return AuthAPI.requestPasswordReset(formData)
                  .then(
                    (data) => dispatch(requestPasswordResetSuccess(data.location)),
                    (data) => dispatch(requestPasswordResetFailure(data.responseJSON))
                  );
  }
}


function requestPasswordResetRequest(email) {
  return {
    type: REQ_PW_RESET_REQUEST,
    email,
  }
}


function requestPasswordResetSuccess(nextURL) {
  return {
    type: REQ_PW_RESET_SUCCESS,
    nextURL,
  }
}


function requestPasswordResetFailure(jsonResponse) {
  return {
    type: REQ_PW_RESET_FAILURE,
    errors: handleErrors(jsonResponse),
  }
}


export const PW_RESET_REQUEST = 'PW_RESET_REQUEST';
export const PW_RESET_SUCCESS = 'PW_RESET_SUCCESS';
export const PW_RESET_FAILURE = 'PW_RESET_FAILURE';


export function passwordReset(formData, url) {
  return dispatch => {
    dispatch(passwordResetRequest());

    // FIXME: ideally we shouldn't be passing in the full URL, but only
    // the necessary bits to construct it
    return AuthAPI.passwordReset(formData, url)
                  .then(
                    (data) => dispatch(passwordResetSuccess()),
                    (data) => dispatch(passwordResetFailure(data.responseJSON))
                  );
  }
}


function passwordResetRequest() {
  return {
    type: PW_RESET_REQUEST,
  }
}


function passwordResetSuccess() {
  return {
    type: PW_RESET_SUCCESS,
  }
}


function passwordResetFailure(jsonResponse) {
  return {
    type: PW_RESET_FAILURE,
    errors: handleErrors(jsonResponse),
  }
}


export const VERIFY_SOCIAL_REQUEST = 'VERIFY_SOCIAL_REQUEST';
export const VERIFY_SOCIAL_SUCCESS = 'VERIFY_SOCIAL_SUCCESS';
export const VERIFY_SOCIAL_FAILURE = 'VERIFY_SOCIAL_FAILURE';


export function verifySocial(formData) {
  return dispatch => {
    dispatch(verifySocialRequest());

    return AuthAPI.verifySocial(formData)
                  .then(
                    (data) => dispatch(verifySocialSuccess(data.location)),
                    (data) => dispatch(verifySocialFailure(data.responseJSON))
                  );
  }
}


function verifySocialRequest() {
  return {
    type: VERIFY_SOCIAL_REQUEST,
  }
}


function verifySocialSuccess(nextURL) {
  return {
    type: VERIFY_SOCIAL_SUCCESS,
    nextURL,
  }
}


function verifySocialFailure(jsonResponse) {
  return {
    type: VERIFY_SOCIAL_FAILURE,
    errors: handleErrors(jsonResponse),
  }
}
