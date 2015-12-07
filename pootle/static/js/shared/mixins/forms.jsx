/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import _ from 'underscore';

import BackboneMixin from './backbone';


export const FormValidationMixin = {

  getInitialState() {
    return {
      errors: {},
    };
  },

  clearValidation() {
    this.setState({errors: {}});
  },

  validateResponse(xhr) {
    // XXX: should this also check for HTTP 500, 404 etc.?
    const response = JSON.parse(xhr.responseText);
    this.setState({errors: response.errors});
  },


  /* Layout */

  renderSingleError(errorMsg, i) {
    return <li key={i}>{errorMsg}</li>;
  },


  /* Renders form's global errors. These errors come in a special
   * `__all__` field */
  renderAllFormErrors() {
    const { errors } = this.state;

    if (errors.hasOwnProperty('__all__')) {
      return (
        <ul className="errorlist errorlist-all">
          {errors.__all__.map(this.renderSingleError)}
        </ul>
      );
    }

    return null;
  },

};


/*
 *
 * Includes:
 *  - server-side validation
 *  - dirtyness status
 *
 * Component using this mixin need to define a `fields` property
 * (array of strings) indicating which model fields to use.
 *
 * Form's behavior can be extended by implementing the following methods:
 *  - `handleSuccess (model)`:
 *    called in the `model.save()`'s success callback
 *  - `handleError (xhr)`:
 *    called in the `model.save()`'s error callback
 */
export const FormMixin = {
  mixins: [FormValidationMixin],

  /* Lifecycle */

  getInitialState() {
    return {
      isDirty: false,
    };
  },


  /* Handlers */

  handleChange(name, value) {
    const newData = _.extend({}, this.state.formData);
    newData[name] = value;
    const isDirty = !_.isEqual(newData, this.initialData);
    this.setState({formData: newData, isDirty: isDirty});
  },

  handleFormSuccess() {
    // Cleanup state
    this.clearValidation();
    this.initialData = _.extend({}, this.state.formData);
    this.setState({
      isDirty: false,
    });

    if (this.handleSuccess) {
      this.handleSuccess(this.getResource());
    }
  },

  handleFormError(xhr) {
    this.validateResponse(xhr);

    if (this.handleError) {
      this.handleError(xhr);
    }
  },

};


/*
 * Backbone model form mixin.
 * Like `FormMixin` but specialized for BB models.
 */
export const ModelFormMixin = {
  mixins: [BackboneMixin, FormMixin],

  propTypes: {
    model: React.PropTypes.object.isRequired,
  },


  /* Lifecycle */

  getInitialState() {
    this.initialData = _.pick(this.getResource().toJSON(), this.fields);
    return {
      formData: _.extend({}, this.initialData),
    };
  },

  componentDidMount() {
    if (_.isUndefined(this.fields)) {
      throw new Error(
        'To use ModelFormMixin, you must define a `fields` property.'
      );
    }
    if (!_.isArray(this.fields)) {
      throw new Error('The `fields` property must be an array.');
    }
  },

  /* BackboneMixin */
  getResource() {
    return this.props.model;
  },


  /* Handlers */

  handleFormSubmit(e) {
    e.preventDefault();

    this.getResource().save(this.state.formData, {wait: true})
                      .done(this.handleFormSuccess)
                      .error(this.handleFormError);
  },

};
