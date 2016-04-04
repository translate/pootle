/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import React from 'react';
import { PureRenderMixin } from 'react-addons-pure-render-mixin';

import FormElement from 'components/FormElement';
import FormMixin from 'mixins/FormMixin';

import { gotoScreen, requestPasswordReset } from '../actions';
import AuthContent from './AuthContent';
import RequestPasswordResetProgress from './RequestPasswordResetProgress';


const RequestPasswordResetForm = React.createClass({

  propTypes: {
    canRegister: React.PropTypes.bool.isRequired,
    dispatch: React.PropTypes.func.isRequired,
    formErrors: React.PropTypes.object.isRequired,
    isLoading: React.PropTypes.bool.isRequired,
  },

  mixins: [PureRenderMixin, FormMixin],

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
      this.setState({ errors: nextProps.formErrors });
    }
  },


  /* Handlers */

  handleSignIn(e) {
    e.preventDefault();
    this.props.dispatch(gotoScreen('signIn'));
  },

  handleSignUp(e) {
    e.preventDefault();
    this.props.dispatch(gotoScreen('signUp'));
  },

  handleFormSubmit(e) {
    e.preventDefault();
    this.props.dispatch(requestPasswordReset(this.state.formData));
  },


  /* Others */

  hasData() {
    return this.state.formData.email !== '';
  },


  /* Layout */

  render() {
    if (this.props.isLoading) {
      return <RequestPasswordResetProgress email={this.state.formData.email} />;
    }

    const { errors } = this.state;
    const { formData } = this.state;

    return (
      <AuthContent>
        <form
          method="post"
          onSubmit={this.handleFormSubmit}
        >
          <div className="fields">
            {this.renderAllFormErrors()}
            <FormElement
              autoFocus
              type="email"
              label={gettext('Email Address')}
              help={gettext('Enter your email address, and we will send you a ' +
                            'message with the special link to reset your password.')}
              handleChange={this.handleChange}
              name="email"
              errors={errors.email}
              value={formData.email}
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
      </AuthContent>
    );
  },

});


export default RequestPasswordResetForm;
