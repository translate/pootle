/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

var React = require('react');
var _ = require('underscore');

var BackboneMixin = require('./backbone');


var FormValidationMixin = {

  getInitialState: function () {
    return {
      errors: {},
    };
  },

  clearValidation: function () {
    this.setState({errors: {}});
  },

  validateResponse: function (xhr) {
    // XXX: should this also check for HTTP 500, 404 etc.?
    var response = JSON.parse(xhr.responseText);
    this.setState({errors: response.errors});
  },


  /* Layout */

  renderSingleError: function (errorMsg, i) {
    return <li key={i}>{errorMsg}</li>;
  },


  /* Renders form's global errors. These errors come in a special
   * `__all__` field */
  renderAllFormErrors: function () {
    var errors = this.state.errors;

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
var FormMixin = {
  mixins: [FormValidationMixin],

  /* Lifecycle */

  getInitialState: function () {
    return {
      isDirty: false,
    };
  },


  /* Handlers */

  handleChange: function (name, value) {
    var newData = _.extend({}, this.state.formData);
    newData[name] = value;
    var isDirty = !_.isEqual(newData, this.initialData);
    this.setState({formData: newData, isDirty: isDirty});
  },

  handleFormSuccess: function () {
    // Cleanup state
    this.clearValidation();
    this.initialData = _.extend({}, this.state.formData);
    this.setState({
      isDirty: false,
    });

    this.handleSuccess && this.handleSuccess(this.getResource());
  },

  handleFormError: function (xhr) {
    this.validateResponse(xhr);

    this.handleError && this.handleError(xhr);
  },

};


/*
 * Backbone model form mixin.
 * Like `FormMixin` but specialized for BB models.
 */
var ModelFormMixin = {
  mixins: [BackboneMixin, FormMixin],

  propTypes: {
    model: React.PropTypes.object.isRequired,
  },


  /* Lifecycle */

  getInitialState: function () {
    this.initialData = _.pick(this.getResource().toJSON(), this.fields);
    return {
      formData: _.extend({}, this.initialData),
    };
  },

  componentDidMount: function () {
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
  getResource: function () {
    return this.props.model;
  },


  /* Handlers */

  handleFormSubmit: function (e) {
    e.preventDefault();

    this.getResource().save(this.state.formData, {wait: true})
                      .done(this.handleFormSuccess)
                      .error(this.handleFormError);
  },

};


module.exports = {
  FormMixin: FormMixin,
  FormValidationMixin: FormValidationMixin,
  ModelFormMixin: ModelFormMixin,
};
