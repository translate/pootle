/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import { PureRenderMixin } from 'react-addons-pure-render-mixin';

import Tab from 'components/Tab';
import Tabs from 'components/Tabs';
import cookie from 'utils/cookie';

import AuthProgress from './AuthProgress';
import SignInForm from './SignInForm';
import SocialSignInForm from './SocialSignInForm';


const SIGNIN_TAB_COOKIE_NAME = 'pootle-auth-signin-tab';


const SignInPanel = React.createClass({

  propTypes: {
    canRegister: React.PropTypes.bool.isRequired,
    formErrors: React.PropTypes.object.isRequired,
    isLoading: React.PropTypes.bool.isRequired,
    socialAuthProviders: React.PropTypes.array.isRequired,
    redirectTo: React.PropTypes.string,
  },

  mixins: [PureRenderMixin],

  /* Handlers */

  handleChange(index) {
    cookie(SIGNIN_TAB_COOKIE_NAME, index, { path: '/' });
  },


  /* Layout */

  render() {
    if (this.props.redirectTo) {
      return <AuthProgress msg={gettext('Signed in. Redirecting...')} />;
    }

    if (!this.props.socialAuthProviders.length) {
      return (
        <SignInForm {...this.props} />
      );
    }

    const initialTabIndex = parseInt(cookie(SIGNIN_TAB_COOKIE_NAME), 10) || 0;

    return (
      <Tabs onChange={this.handleChange} initialTab={initialTabIndex}>
        <Tab title={gettext('Social Services')}>
          <SocialSignInForm {...this.props} />
        </Tab>
        <Tab title={gettext('Login / Password')}>
          <SignInForm {...this.props} />
        </Tab>
      </Tabs>
    );
  },

});


export default SignInPanel;
