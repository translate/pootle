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

import AccountActivation from './AccountActivation';
import AccountInactive from './AccountInactive';
import AuthWindow from './AuthWindow';
import EmailConfirmation from './EmailConfirmation';
import RequestPasswordResetForm from './RequestPasswordResetForm';
import RequestPasswordResetSent from './RequestPasswordResetSent';
import PasswordResetForm from './PasswordResetForm';
import SignInPanel from './SignInPanel';
import SignUpForm from './SignUpForm';
import SocialAuthError from './SocialAuthError';
import SocialVerification from './SocialVerification';


let AuthController = React.createClass({

  propTypes: {
    // Optionally overrides state
    initialAction: React.PropTypes.string,
    initialActionData: React.PropTypes.object,
    initialScreen: React.PropTypes.string,

    canContact: React.PropTypes.bool.isRequired,
    canRegister: React.PropTypes.bool.isRequired,
    onClose: React.PropTypes.func.isRequired,
    socialAuthProviders: React.PropTypes.array.isRequired,
    socialError: React.PropTypes.object,
    tokenFailed: React.PropTypes.bool,
  },

  getDefaultProps() {
    return {
      initialAction: null,
      initialActionData: {},
      initialScreen: 'signIn',
      tokenFailed: false,
    };
  },


  /* Lifecycle */

  componentWillMount() {
    let authActions = this.props.flux.getActions('auth');
    if (this.props.initialScreen) {
      authActions.gotoScreen(this.props.initialScreen);
    }
    if (this.props.initialAction) {
      authActions[this.props.initialAction](this.props.initialActionData);
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

  getScreen(screenName, props) {
    // FIXME: use react-router
    switch (screenName) {
      case 'signIn':
        let hasSocialAuth = props.socialAuthProviders.length !== 0;
        return {
          title: hasSocialAuth ? gettext('Sign In With...') : gettext('Sign In'),
          content: SignInPanel,
        };
        break;

      case 'inactive':
        return {
          title: gettext('Account Inactive'),
          content: AccountInactive,
        };
        break;

      case 'signUp':
        return {
          title: gettext('Sign Up'),
          content: SignUpForm,
        };
        break;

      case 'activation':
        return {
          title: gettext('Account Activation'),
          content: AccountActivation,
        };
        break;

      case 'emailConfirmation':
        return {
          title: gettext('Email Confirmation'),
          content: EmailConfirmation,
        };
        break;

      case 'requestPasswordReset':
        return {
          title: gettext('Reset Your Password'),
          content: RequestPasswordResetForm,
        };
        break;

      case 'requestPasswordResetSent':
        return {
          title: gettext('Reset Your Password'),
          content: RequestPasswordResetSent,
        };
        break;

      case 'passwordReset':
        return {
          title: gettext('Reset Your Password'),
          content: PasswordResetForm,
        };
        break;

      case 'socialAuthError':
        return {
          title: gettext('Oops...'),
          content: SocialAuthError,
        };
        break;

      case 'socialVerification':
        return {
          title: gettext('Social Verification'),
          content: SocialVerification,
        };
        break;
    }
  },

  render() {
    let currentScreen = this.getScreen(this.props.screen, this.props);
    let ContentComponent = currentScreen.content;

    return (
      <AuthWindow
        canContact={this.props.canContact}
        title={currentScreen.title}
        onClose={this.props.onClose}
      >
        <ContentComponent
          canRegister={this.props.canRegister}
          onClose={this.props.onClose}
          socialAuthProviders={this.props.socialAuthProviders}
          socialError={this.props.socialError}
          tokenFailed={this.props.tokenFailed}
          {...this.props}
        />
      </AuthWindow>
    );
  }

});


export default AuthController;
