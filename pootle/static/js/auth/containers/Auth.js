/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import { connect } from 'react-redux';

import { gotoScreen, requestPasswordReset } from '../actions';

import AccountActivation from '../components/AccountActivation';
import AccountInactive from '../components/AccountInactive';
import AuthWindow from '../components/AuthWindow';
import EmailConfirmation from '../components/EmailConfirmation';
import RequestPasswordResetForm from '../components/RequestPasswordResetForm';
import RequestPasswordResetSent from '../components/RequestPasswordResetSent';
import PasswordResetForm from '../components/PasswordResetForm';
import SignInPanel from '../components/SignInPanel';
import SignUpForm from '../components/SignUpForm';
import SocialAuthError from '../components/SocialAuthError';
import SocialVerification from '../components/SocialVerification';


const Auth = React.createClass({

  propTypes: {
    // Optionally overrides state
    initPasswordReset: React.PropTypes.object,
    initialScreen: React.PropTypes.string,

    canContact: React.PropTypes.bool.isRequired,
    canRegister: React.PropTypes.bool.isRequired,
    dispatch: React.PropTypes.func.isRequired,
    onClose: React.PropTypes.func.isRequired,
    screen: React.PropTypes.string.isRequired,
    socialAuthProviders: React.PropTypes.array.isRequired,
    socialError: React.PropTypes.object,
    tokenFailed: React.PropTypes.bool,
  },

  getDefaultProps() {
    return {
      initPasswordReset: null,
      tokenFailed: false,
    };
  },


  /* Lifecycle */

  componentWillMount() {
    if (this.props.initialScreen) {
      this.props.dispatch(gotoScreen(this.props.initialScreen));
    }
    if (this.props.initPasswordReset) {
      this.props.dispatch(requestPasswordReset(this.props.initPasswordReset));
    }
  },

  componentWillReceiveProps(nextProps) {
    if (nextProps.redirectTo !== null) {
      const currentLocation = window.location.pathname + window.location.hash;
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
      case 'signIn': {
        const hasSocialAuth = props.socialAuthProviders.length !== 0;
        return {
          title: hasSocialAuth ? gettext('Sign In With...') : gettext('Sign In'),
          content: SignInPanel,
        };
      }

      case 'inactive':
        return {
          title: gettext('Account Inactive'),
          content: AccountInactive,
        };

      case 'signUp':
        return {
          title: gettext('Sign Up'),
          content: SignUpForm,
        };

      case 'activation':
        return {
          title: gettext('Account Activation'),
          content: AccountActivation,
        };

      case 'emailConfirmation':
        return {
          title: gettext('Email Confirmation'),
          content: EmailConfirmation,
        };

      case 'requestPasswordReset':
        return {
          title: gettext('Reset Your Password'),
          content: RequestPasswordResetForm,
        };

      case 'requestPasswordResetSent':
        return {
          title: gettext('Reset Your Password'),
          content: RequestPasswordResetSent,
        };

      case 'passwordReset':
        return {
          title: gettext('Reset Your Password'),
          content: PasswordResetForm,
        };

      case 'socialAuthError':
        return {
          title: gettext('Oops...'),
          content: SocialAuthError,
        };

      case 'socialVerification':
        return {
          title: gettext('Social Verification'),
          content: SocialVerification,
        };

      default:
        break;
    }

    return {};
  },

  render() {
    const currentScreen = this.getScreen(this.props.screen, this.props);
    const ContentComponent = currentScreen.content;

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
  },

});


export default connect(state => state.auth)(Auth);
