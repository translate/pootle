/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import React from 'react';

import { gotoScreen, signIn } from '../actions';
import { FormElement } from 'components/forms';
import { FormMixin } from 'mixins/forms';


const SignInForm = React.createClass({
  mixins: [FormMixin],

  propTypes: {
    canRegister: React.PropTypes.bool.isRequired,
    formErrors: React.PropTypes.object.isRequired,
    isLoading: React.PropTypes.bool.isRequired,
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
    this.props.dispatch(gotoScreen('requestPasswordReset'));
  },

  handleSignUp(e) {
    e.preventDefault();
    this.props.dispatch(gotoScreen('signUp'));
  },

  handleFormSubmit(e) {
    e.preventDefault();
    let nextURL = window.location.pathname + window.location.hash;
    this.props.dispatch(signIn(this.state.formData, nextURL));
  },


  /* Others */

  hasData() {
    let { formData } = this.state;
    return formData.login !== '' && formData.password !== '';
  },


  /* Layout */

  render() {
    let { errors } = this.state;
    let { formData } = this.state;

    let signUp = this.props.canRegister ?
      <a href="#" onClick={this.handleSignUp}>
        {gettext('Sign up as a new user')}
      </a> :
      <p>{gettext('Creating new user accounts is prohibited.')}</p>;

    return (
      <form
        method="post"
        onSubmit={this.handleFormSubmit}
      >
        <div className="fields">
          <FormElement
            attribute="login"
            label={gettext('Username')}
            autoFocus={true}
            handleChange={this.handleChange}
            formData={formData}
            errors={errors}
          />
          <FormElement
            type="password"
            attribute="password"
            label={gettext('Password')}
            handleChange={this.handleChange}
            formData={formData}
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
              disabled={!this.hasData() || this.props.isLoading}
              value={gettext('Sign In')}
            />
          </div>
          <div>
            {signUp}
          </div>
        </div>
      </form>
    );
  },

});


export default SignInForm;
