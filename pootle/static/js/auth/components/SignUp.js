/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import React from 'react';
import assign from 'object-assign';
import { PureRenderMixin } from 'react/addons';

import { FormElement } from 'components/forms';
import { FormMixin } from 'mixins/forms';


export let SignUpForm = React.createClass({
  mixins: [FormMixin],

  propTypes: {
    formErrors: React.PropTypes.object.isRequired,
  },


  /* Lifecycle */

  getInitialState() {
    this.initialData = {
      username: '',
      email: '',
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


  /* State-changing handlers */

  handleSignUp(e) {
    e.preventDefault();
    this.props.flux.getActions('auth').gotoScreen('signIn');
  },

  handleFormSubmit(e) {
    e.preventDefault();

    this.props.flux.getActions('auth').signUp(this.state.formData);
  },


  /* Others */

  hasData() {
    let data = this.state.formData;
    return (data.username !== '' && data.email !== '' &&
            data.password1 !== '' && data.password2 !== '');
  },


  /* Layout */

  render() {
    let errors = this.state.errors;
    let data = this.state.formData;

    return (
      <form
        method="post"
        onSubmit={this.handleFormSubmit}>
        <div className="fields">
          <FormElement
            attribute="username"
            label={gettext('Username')}
            autoFocus={true}
            handleChange={this.handleChange}
            formData={data}
            errors={errors}
          />
          <FormElement
            attribute="email"
            label={gettext('Email')}
            handleChange={this.handleChange}
            formData={data}
            errors={errors}
          />
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
              value={gettext('Sign Up')}
            />
          </div>
          <div>
            <a href="#" onClick={this.handleSignUp}>
              {gettext('Sign in as an existing user')}
            </a>
          </div>
        </div>
      </form>
    );
  }
});


export let AccountActivation = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    onClose: React.PropTypes.func.isRequired,
    signUpEmail: React.PropTypes.string,
  },


  /* Layout */

  render() {
    let emailLinkMsg;

    if (this.props.signUpEmail) {
      emailLinkMsg = interpolate(
        gettext('We have sent an email to %s containing the special link.'),
        [this.props.signUpEmail]
      );
    } else {
      emailLinkMsg = gettext(
        'We have sent an email to the address you used to register this account containing the special link.'
      );
    }

    let activationWarningMsg = gettext('Your account needs activation.');
    let instructionsMsg = gettext('Please follow that link to continue the account creation.');

    return (
      <div className="actions">
        <p>{activationWarningMsg}</p>
        <p>{emailLinkMsg}</p>
        <p>{instructionsMsg}</p>
        {this.props.signUpEmail &&
          <div>
            <button
              className="btn btn-primary"
              onClick={this.props.onClose}
            >
              {gettext('Close')}
            </button>
          </div>
        }
      </div>
    );
  }

});
