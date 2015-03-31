/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import { Store } from 'flummox';


export default class AuthStore extends Store {

  constructor(flux) {
    super();

    let authActions = flux.getActions('auth');

    // TODO: review if each of these can go in its own store
    this.register(authActions.gotoScreen, this.handleGotoScreen);
    this.registerAsync(authActions.signIn, this.handleSignInBegin,
                                           this.handleSignInSuccess,
                                           this.handleSignInError);
    this.registerAsync(authActions.signUp, this.handleSignUpBegin,
                                           this.handleSignUpSuccess,
                                           this.handleSignUpError);
    this.registerAsync(authActions.requestPasswordReset,
                       this.handleRequestPasswordResetBegin,
                       this.handleRequestPasswordResetSuccess,
                       this.handleRequestPasswordResetError);
    this.registerAsync(authActions.passwordReset, this.handlePasswordResetBegin,
                                                  this.handlePasswordResetSuccess,
                                                  this.handlePasswordResetError);

    this.state = {
      screen: 'signIn',

      redirectTo: null,
      resetEmail: null,
      signUpEmail: null,

      // FIXME: check if isLoading is actually needed everywhere
      isLoading: false, // Should be part of some generic 'request' store?
      formErrors: {}, // Should be part of some generic 'error' store?
    };
  }


  /* Screen */

  handleGotoScreen(screenName) {
    this.setState({screen: screenName});
  }


  /* Sign In */

  handleSignInBegin(reqData, nextURL) {
    this.setState({isLoading: true});
  }

  handleSignInSuccess(newLocation) {
    // HACKISH: allauth's XHR responses are not very informative, so
    // it's necessary to do some guesswork around URLs in order to know
    // what the actual response is supposed to mean
    if (newLocation.indexOf('confirm-email') !== -1) {
      this.setState({
        screen: 'activation',
        email: null,
      });
    } else if (newLocation.indexOf('inactive') !== -1) {
      this.setState({
        // TODO: implement screen
        screen: 'inactive',
        email: null,
      });
    } else {
      this.setState({redirectTo: newLocation});
    }
    this.setState({
      isLoading: false,
      formErrors: {},
    });
  }

  handleSignInError(errors) {
    this.setState({
      isLoading: false,
      formErrors: errors,
    });
  }


  /* Sign Up */

  handleSignUpBegin(reqData) {
    this.setState({
      isLoading: true,
      signUpEmail: reqData.email,
    });
  }

  handleSignUpSuccess() {
    this.setState({
      screen: 'activation',
      isLoading: false,
      formErrors: {},
    });
  }

  handleSignUpError(errors) {
    this.setState({
      isLoading: false,
      formErrors: errors,
    });
  }


  /* Request Password Reset */

  handleRequestPasswordResetBegin(reqData) {
    this.setState({
      isLoading: true,
      resetEmail: reqData.email,
    });
  }

  handleRequestPasswordResetSuccess() {
    this.setState({
      screen: 'requestPasswordResetSent',
      formErrors: {},
      isLoading: false,
    });
  }

  handleRequestPasswordResetError(errors) {
    this.setState({
      isLoading: false,
      formErrors: errors,
    });
  }


  /* Password Reset */

  handlePasswordResetBegin(reqData, url) {
    this.setState({isLoading: true});
  }

  handlePasswordResetSuccess(response) {
    this.setState({
      formErrors: {},
      isLoading: false,
      // FIXME: hard-coding redirect path because of django-allauth#735
      redirectTo: l('/'),
    });
  }

  handlePasswordResetError(errors) {
    this.setState({
      isLoading: false,
      formErrors: errors,
    });
  }

}
