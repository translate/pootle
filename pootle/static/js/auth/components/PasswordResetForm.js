/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import React from 'react';
import { PureRenderMixin } from 'react/addons';

import { FormElement } from 'components/forms';
import { FormMixin } from 'mixins/forms';

import { gotoScreen, passwordReset } from '../actions';
import AuthContent from './AuthContent';
import AuthProgress from './AuthProgress';


const PasswordResetForm = React.createClass({
  mixins: [PureRenderMixin, FormMixin],

  propTypes: {
    formErrors: React.PropTypes.object.isRequired,
    isLoading: React.PropTypes.bool.isRequired,
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
    this.props.dispatch(gotoScreen('requestPasswordReset'));
  },

  handleFormSubmit(e) {
    e.preventDefault();

    let url = window.location.pathname;
    this.props.dispatch(passwordReset(this.state.formData, url));
  },


  /* Others */

  hasData() {
    let { formData } = this.state;
    return (formData.password1 !== '' && formData.password2 !== '' &&
            formData.password1 === formData.password2);
  },


  /* Layout */

  renderTokenFailed() {
    return (
      <AuthContent>
        <p>{gettext('The password reset link was invalid, possibly because it has already been used. Please request a new password reset.')}</p>
        <div className="actions">
          <button
            className="btn btn-primary"
            onClick={this.handlePasswordReset}
          >
            {gettext('Reset Password')}
          </button>
        </div>
      </AuthContent>
    );
  },

  render() {
    if (this.props.tokenFailed) {
      return this.renderTokenFailed();
    }
    if (this.props.redirectTo) {
      return <AuthProgress msg={gettext('Password changed, signing in...')} />
    }

    let { errors } = this.state;
    let { formData } = this.state;

    return (
      <AuthContent>
        <form
          method="post"
          onSubmit={this.handleFormSubmit}>
          <div className="fields">
            <FormElement
              type="password"
              attribute="password1"
              label={gettext('Password')}
              autoFocus={true}
              handleChange={this.handleChange}
              formData={formData}
              errors={errors}
            />
            <FormElement
              type="password"
              attribute="password2"
              label={gettext('Repeat Password')}
              handleChange={this.handleChange}
              formData={formData}
              errors={errors}
            />
          </div>
          {this.renderAllFormErrors()}
          <div className="actions">
            <div>
              <input
                type="submit"
                className="btn btn-primary"
                disabled={!this.hasData() | this.props.isLoading}
                value={gettext('Set New Password')}
              />
            </div>
            <div>
              <p>{gettext('After changing your password you will sign in automatically.')}</p>
            </div>
          </div>
        </form>
      </AuthContent>
    );
  },

});


export default PasswordResetForm;
