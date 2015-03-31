/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import React from 'react';
import FluxComponent from 'flummox/component';

import AuthWindow from './AuthWindow';
import { RequestPasswordResetForm, RequestPasswordResetSent, PasswordResetForm }
       from './PasswordReset';
import { AccountInactive, SignInPanel } from './SignIn';
import { AccountActivation, SignUpForm } from './SignUp';


// FIXME: use react-router
const screensMap = {
  signIn: {
    title: gettext('Sign In With...'),
    content: SignInPanel,
  },
  inactive: {
    title: gettext('Account Inactive'),
    content: AccountInactive,
  },
  signUp: {
    title: gettext('Sign Up'),
    content: SignUpForm,
  },
  activation: {
    title: gettext('Account Activation'),
    content: AccountActivation,
  },
  requestPasswordReset: {
    title: gettext('Reset Your Password'),
    content: RequestPasswordResetForm,
  },
  requestPasswordResetSent: {
    title: gettext('Reset Your Password'),
    content: RequestPasswordResetSent,
  },
  passwordReset: {
    title: gettext('Reset Your Password'),
    content: PasswordResetForm,
  },
};


let AuthController = React.createClass({

  propTypes: {
    // Optionally overrides state
    initialScreen: React.PropTypes.string,
    onClose: React.PropTypes.func.isRequired,
    socialAuthProviders: React.PropTypes.array.isRequired,
    tokenFailed: React.PropTypes.bool,
  },

  getDefaultProps() {
    return {
      initialScreen: 'signIn',
      tokenFailed: false,
    };
  },


  /* Lifecycle */

  componentDidMount() {
    // FIXME: this code should live in `componentWillMount()`, but because
    // we're in 0.12 and react#1245 we're workingn around it here
    if (this.props.initialScreen) {
      this.props.flux.getActions('auth').gotoScreen(this.props.initialScreen);
    }
  },

  componentWillReceiveProps(nextProps) {
    if (nextProps.redirectTo !== null) {
      let currentLocation = window.location.pathname + window.location.hash;
      if (currentLocation !== nextProps.redirectTo) {
        window.location = nextProps.redirectTo;
      } else {
        window.location.reload();
      }
    }
  },


  /* Layout */

  render() {
    let currentScreen = screensMap[this.props.screen];
    let ContentComponent = currentScreen.content;

    return (
      <AuthWindow
        title={currentScreen.title}
        onClose={this.props.onClose}
      >
        <ContentComponent
          canRegister={this.props.canRegister}
          onClose={this.props.onClose}
          socialAuthProviders={this.props.socialAuthProviders}
          tokenFailed={this.props.tokenFailed}
          {...this.props}
        />
      </AuthWindow>
    );
  }

});


export default AuthController;
