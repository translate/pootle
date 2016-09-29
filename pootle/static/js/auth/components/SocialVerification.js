/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import React from 'react';

import { t } from 'utils/i18n';
import FormElement from 'components/FormElement';
import FormMixin from 'mixins/FormMixin';

import { gotoScreen, verifySocial } from '../actions';
import AuthProgress from './AuthProgress';


const SocialVerification = React.createClass({

  propTypes: {
    dispatch: React.PropTypes.func.isRequired,
    email: React.PropTypes.string.isRequired,
    formErrors: React.PropTypes.object.isRequired,
    isLoading: React.PropTypes.bool.isRequired,
    providerName: React.PropTypes.string.isRequired,
    redirectTo: React.PropTypes.string,
  },

  mixins: [FormMixin],

  getInitialState() {
    // XXX: initialData required by `FormMixin`; this is really OBSCURE
    this.initialData = {
      password: '',
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

  handleRequestPasswordReset(e) {
    e.preventDefault();
    this.props.dispatch(gotoScreen('requestPasswordReset'));
  },

  handleFormSubmit(e) {
    e.preventDefault();
    this.props.dispatch(verifySocial(this.state.formData));
  },


  /* Others */

  hasData() {
    return this.state.formData.password !== '';
  },


  /* Layout */

  render() {
    if (this.props.redirectTo) {
      return <AuthProgress msg={gettext('Signed in. Redirecting...')} />;
    }

    const { errors } = this.state;
    const { formData } = this.state;

    const verificationMsg = t(
      'We found a user with <span>%(email)s</span> email in our system. ' +
      'Please provide the password to finish the sign in procedure. This ' +
      'is a one-off procedure, which will establish a link between your ' +
      'Pootle and %(provider)s accounts.',
      { email: this.props.email, provider: this.props.providerName }
    );

    return (
      <div className="actions">
        <p dangerouslySetInnerHTML={{ __html: verificationMsg }} />
        <div>
          <form
            method="post"
            onSubmit={this.handleFormSubmit}
          >
            <div className="fields">
              <FormElement
                type="password"
                label={gettext('Password')}
                handleChange={this.handleChange}
                name="password"
                errors={errors.password}
                value={formData.password}
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
                  disabled={!this.hasData() | this.props.isLoading}
                  value={gettext('Sign In')}
                />
              </div>
            </div>
          </form>
        </div>
      </div>
    );
  },

});


export default SocialVerification;
