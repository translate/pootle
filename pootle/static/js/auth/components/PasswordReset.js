/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import assign from 'object-assign';
import React from 'react';
import { PureRenderMixin } from 'react/addons';

import { FormElement } from 'components/forms';
import { FormMixin } from 'mixins/forms';


export let RequestPasswordResetForm = React.createClass({
  mixins: [PureRenderMixin, FormMixin],

  propTypes: {
    formErrors: React.PropTypes.object.isRequired,
    canRegister: React.PropTypes.bool.isRequired,
    isLoading: React.PropTypes.bool.isRequired,
  },


  /* Lifecycle */

  getInitialState() {
    this.initialData = {
      email: '',
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

  handleSignIn(e) {
    e.preventDefault();
    this.props.flux.getActions('auth').gotoScreen('signIn');
  },

  handleSignUp(e) {
    e.preventDefault();
    this.props.flux.getActions('auth').gotoScreen('signUp');
  },

  handleFormSubmit(e) {
    e.preventDefault();
    this.props.flux.getActions('auth').requestPasswordReset(this.state.formData);
  },


  /* Others */

  hasData() {
    return this.state.formData.email !== '';
  },


  /* Layout */

  render() {
    if (this.props.isLoading) {
      return <SendingProgress email={this.state.formData.email} />;
    }

    let errors = this.state.errors;
    let data = this.state.formData;

    return (
      <form
        method="post"
        onSubmit={this.handleFormSubmit}>
        <div className="fields">
          {this.renderAllFormErrors()}
          <FormElement
            attribute="email"
            label={gettext('Email Address')}
            help={gettext('Enter your email address, and we will send you a message with the special link to reset your password.')}
            autoFocus={true}
            handleChange={this.handleChange}
            formData={data}
            errors={errors}
          />
        </div>
        <div className="actions">
          <div>
            <a href="#" onClick={this.handleSignIn}>
              {gettext('No, thanks')}
            </a>
          </div>
          <div>
            <input
              type="submit"
              className="btn btn-primary"
              disabled={!this.hasData()}
              value={gettext('Send Email')}
            />
          </div>
          {this.props.canRegister &&
            <div>
              <a href="#" onClick={this.handleSignUp}>
                {gettext('Sign up as a new user')}
              </a>
            </div>
          }
        </div>
      </form>
    );
  }

});


export let RequestPasswordResetSent = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    resetEmail: React.PropTypes.string.isRequired,
    isLoading: React.PropTypes.bool.isRequired,
  },


  /* Handlers */

  handleResendEmail() {
    this.props.flux.getActions('auth').requestPasswordReset({email: this.props.resetEmail});
  },


  /* Layout */

  render() {
    if (this.props.isLoading) {
      return <SendingProgress email={this.props.resetEmail} />;
    }

    let emailLinkMsg = interpolate(
      gettext('Thank you, we have sent an email to %s containing the special link.'),
      [this.props.resetEmail]
    );
    let instructionsMsg = gettext('Please follow that link to continue the password reset procedure.');
    let resendMsg = gettext("Didn't receive an email? Check if it was accidentally filtered out as spam, or try getting another copy of the email.");

    return (
      <div className="actions">
        <p>{emailLinkMsg}</p>
        <p>{instructionsMsg}</p>
        <hr />
        <p>{resendMsg}</p>
        <div>
          <button
            className="btn btn-primary"
            onClick={this.handleResendEmail}
          >
            {gettext('Resend Email')}
          </button>
        </div>
      </div>
    );
  }

});


let SendingProgress = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    email: React.PropTypes.string.isRequired,
  },

  render() {
    let email = this.props.email;
    let sendingEmailMsg = interpolate(gettext('Sending email to %s...'), [email]);
    // FIXME: use flexbox when possible
    let style = {
      outer: {
        display: 'table',
        height: '20em',
        width: '100%',
        textAlign: 'center',
      },
      inner: {
        display: 'table-cell',
        verticalAlign: 'middle',
      },
    };

    return (
      <div style={style.outer}>
        <div style={style.inner}>
          <p>{sendingEmailMsg}</p>
        </div>
      </div>
    );
  },

});


export let PasswordResetForm = React.createClass({
  mixins: [PureRenderMixin, FormMixin],

  propTypes: {
    formErrors: React.PropTypes.object.isRequired,
    tokenFailed: React.PropTypes.bool.isRequired,
  },


  /* Lifecycle */

  getInitialState() {
    this.initialData = {
      password1: '',
      password2: '',
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

  handlePasswordReset(e) {
    e.preventDefault();
    this.props.flux.getActions('auth').gotoScreen('requestPasswordReset');
  },

  handleFormSubmit(e) {
    e.preventDefault();

    let url = window.location.pathname;
    this.props.flux.getActions('auth').passwordReset(this.state.formData, url);
  },


  /* Others */

  hasData() {
    let data = this.state.formData;
    return (data.password1 !== '' && data.password2 !== '');
  },


  /* Layout */

  renderTokenFailed() {
    return (
      <div>
        <p>{gettext('The password reset link was invalid, possibly because it has already been used. Please request a new password reset.')}</p>
        <div className="actions">
          <button
            className="btn btn-primary"
            onClick={this.handlePasswordReset}
          >
            {gettext('Reset Password')}
          </button>
        </div>
      </div>
    );
  },

  render() {
    if (this.props.tokenFailed) {
      return this.renderTokenFailed();
    }

    let errors = this.state.errors;
    let data = this.state.formData;

    return (
      <form
        method="post"
        onSubmit={this.handleFormSubmit}>
        <div className="fields">
          <FormElement
            type="password"
            attribute="password1"
            label={gettext('Password')}
            handleChange={this.handleChange}
            formData={data}
            errors={errors}
          />
          <FormElement
            type="password"
            attribute="password2"
            label={gettext('Repeat Password')}
            handleChange={this.handleChange}
            formData={data}
            errors={errors}
          />
        </div>
        {this.renderAllFormErrors()}
        <div className="actions">
          <div>
            <input
              type="submit"
              className="btn btn-primary"
              disabled={!this.hasData()}
              value={gettext('Set New Password')}
            />
          </div>
        </div>
      </form>
    );
  }

});
