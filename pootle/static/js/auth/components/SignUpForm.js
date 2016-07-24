/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import assign from 'object-assign';

import { gotoScreen, signUp } from '../actions';
import FormElement from 'components/FormElement';
import FormMixin from 'mixins/FormMixin';


const SignUpForm = React.createClass({

  propTypes: {
    dispatch: React.PropTypes.func.isRequired,
    formErrors: React.PropTypes.object.isRequired,
    isLoading: React.PropTypes.bool.isRequired,
  },

  mixins: [FormMixin],

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
      this.setState({ errors: nextProps.formErrors });
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
    const { formData } = this.state;
    return (formData.username !== '' && formData.email !== '' &&
            formData.password1 !== '' && formData.password2 !== '');
  },


  /* Layout */

  render() {
    const { errors } = this.state;
    const { formData } = this.state;

    return (
      <form
        method="post"
        onSubmit={this.handleFormSubmit}
      >
        <div className="fields">
          <FormElement
            autoFocus
            label={gettext('Username')}
            handleChange={this.handleChange}
            name="username"
            errors={errors.username}
            value={formData.username}
            dir="ltr"
          />
          <FormElement
            label={gettext('Email')}
            handleChange={this.handleChange}
            name="email"
            errors={errors.email}
            value={formData.email}
            dir="ltr"
          />
          <FormElement
            type="password"
            label={gettext('Password')}
            handleChange={this.handleChange}
            name="password1"
            errors={errors.password1}
            value={formData.password1}
            dir="ltr"
          />
          <FormElement
            type="password"
            label={gettext('Repeat Password')}
            handleChange={this.handleChange}
            name="password2"
            errors={errors.password2}
            value={formData.password2}
            dir="ltr"
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
