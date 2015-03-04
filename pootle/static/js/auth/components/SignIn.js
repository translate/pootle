/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import 'jquery-cookie';
import assign from 'object-assign';
import React from 'react';
import { PureRenderMixin } from 'react/addons';

import { FormElement } from 'components/forms';
import { Tabs, Tab } from 'components/Tabs';
import { FormMixin } from 'mixins/forms';


const SIGNIN_TAB_COOKIE_NAME = 'pootle-auth-signin-tab';


export let SignInPanel = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    formErrors: React.PropTypes.object.isRequired,
    socialAuthProviders: React.PropTypes.array.isRequired,
    canRegister: React.PropTypes.bool.isRequired,
  },


  /* Handlers */

  handleChange(index) {
    $.cookie(SIGNIN_TAB_COOKIE_NAME, index);
  },


  /* Layout */

  render() {
    if (!this.props.socialAuthProviders.length) {
      return (
        <SignInForm {...this.props} />
      );
    }

    let initialTabIndex = parseInt($.cookie(SIGNIN_TAB_COOKIE_NAME), 10) || 0;

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
  }

});


let SignInForm = React.createClass({
  mixins: [FormMixin],

  propTypes: {
    formErrors: React.PropTypes.object.isRequired,
    canRegister: React.PropTypes.bool.isRequired,
  },


  /* Lifecycle */

  getInitialState() {
    // XXX: initialData required by `FormMixin`; this is really OBSCURE
    this.initialData = {
      login: '',
      password: '',
    };
    return {
      formData: assign({}, this.initialData),
    };
  },

  componentWillReceiveProps(nextProps) {
    if (this.state.errors !== nextProps.formErrors) {
      this.setState({errors: nextProps.formErrors});
    }
  },


  /* Handlers */

  handleRequestPasswordReset(e) {
    e.preventDefault();
    this.props.flux.getActions('auth').gotoScreen('requestPasswordReset');
  },

  handleSignUp(e) {
    e.preventDefault();
    this.props.flux.getActions('auth').gotoScreen('signUp');
  },

  handleFormSubmit(e) {
    e.preventDefault();
    let nextURL = window.location.pathname + window.location.hash;
    this.props.flux.getActions('auth').signIn(this.state.formData, nextURL);
  },


  /* Others */

  hasData() {
    let data = this.state.formData;
    return data.login !== '' && data.password !== '';
  },


  /* Layout */

  render() {
    let errors = this.state.errors;
    let data = this.state.formData;

    let signUp = this.props.canRegister ?
      <a href="#" onClick={this.handleSignUp}>
        {gettext('Sign up as a new user')}
      </a> :
      <p>{gettext('Creating new user accounts is prohibited.')}</p>;

    return (
      <form
        method="post"
        onSubmit={this.handleFormSubmit}>
        <div className="fields">
          <FormElement
            attribute="login"
            label={gettext('Username')}
            autoFocus={true}
            handleChange={this.handleChange}
            formData={data}
            errors={errors}
          />
          <FormElement
            type="password"
            attribute="password"
            label={gettext('Password')}
            handleChange={this.handleChange}
            formData={data}
            errors={errors}
          />
          <div className="actions password-forgotten">
            <a href="#" onClick={this.handleRequestPasswordReset}>
              {gettext('I forgot my password')}
            </a>
          </div>
          {this.renderAllFormErrors()}
        </div>
        <div className="actions">
          <div>
            <input
              type="submit"
              className="btn btn-primary"
              disabled={!this.hasData()}
              value={gettext('Sign In')}
            />
          </div>
          <div>
            {signUp}
          </div>
        </div>
      </form>
    );
  }
});


let SocialSignInForm = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    socialAuthProviders: React.PropTypes.array.isRequired,
  },


  /* Handlers */

  handleClick(url) {
    let nextURL = window.location.pathname + window.location.hash;
    window.location = `${url}?next=${encodeURIComponent(nextURL)}`;
  },


  /* Layout */

  renderSocialAuthButton(socialAuth, index) {
    return (
      <button
        className="btn btn-big"
        key={index}
        onClick={this.handleClick.bind(null, socialAuth.url)}
      >
        {interpolate(gettext('Sign In With %s'), [socialAuth.name])}
      </button>
    );
  },

  render() {
    let signInWarningMsg = gettext('Signing in with an external service for the first time will automatically create an account for you.');

    return (
      <div className="actions">
        {this.props.socialAuthProviders.map(this.renderSocialAuthButton)}
        <hr />
        <p>{signInWarningMsg}</p>
      </div>
    );
  },

});


export let AccountInactive = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    onClose: React.PropTypes.func.isRequired,
  },


  /* Layout */

  render() {
    return (
      <div className="actions">
        <p>{gettext('Your account is inactive because an administrator deactivated it.')}</p>
        <div>
          <button
            className="btn btn-primary"
            onClick={this.props.onClose}
          >
            {gettext('Close')}
          </button>
        </div>
      </div>
    );
  }

});
