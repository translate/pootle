/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import assign from 'object-assign';
import { PureRenderMixin } from 'react/addons';

import { gotoScreen, signUp } from '../actions';
import { FormElement } from 'components/forms';
import { FormMixin } from 'mixins/forms';


const SignUpForm = React.createClass({
  mixins: [FormMixin],

  propTypes: {
    formErrors: React.PropTypes.object.isRequired,
    isLoading: React.PropTypes.bool.isRequired,
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
    this.props.dispatch(gotoScreen('signIn'));
  },

  handleFormSubmit(e) {
    e.preventDefault();
    this.props.dispatch(signUp(this.state.formData));
  },


  /* Others */

  hasData() {
    let { formData } = this.state;
    return (formData.username !== '' && formData.email !== '' &&
            formData.password1 !== '' && formData.password2 !== '');
  },


  /* Layout */

  render() {
    let { errors } = this.state;
    let { formData } = this.state;

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
            formData={formData}
            errors={errors}
          />
          <FormElement
            attribute="email"
            label={gettext('Email')}
            handleChange={this.handleChange}
            formData={formData}
            errors={errors}
          />
          <FormElement
            type="password"
            attribute="password1"
            label={gettext('Password')}
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
  },

});


export default SignUpForm;
