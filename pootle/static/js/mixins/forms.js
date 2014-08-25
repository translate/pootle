'use strict';

var React = require('react');
var _ = require('underscore');

var BackboneMixin = require('./backbone');


var FormValidationMixin = {

  getInitialState: function () {
    return {
      errors: {}
    };
  },

  clearValidation: function () {
    this.setState({errors: {}});
  },

  validateResponse: function (xhr) {
    // XXX: should this also check for HTTP 500, 404 etc.?
    var response = JSON.parse(xhr.responseText);
    this.setState({errors: response.errors});
  }

};


/*
 * Backbone model form mixin.
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
var ModelFormMixin = {
  mixins: [BackboneMixin, FormValidationMixin],

  propTypes: {
    model: React.PropTypes.object.isRequired
  },

  /* BackboneMixin */
  getResource: function () {
    return this.props.model;
  },


  /* Lifecycle */

  getInitialState: function () {
    var initialData = _.pick(this.getResource().toJSON(), this.fields);
    return {
      initialData: _.extend({}, initialData),
      formData: _.extend({}, initialData),
      isDirty: false
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


  /* Handlers */

  handleChange: function (name, value) {
    var newData = _.extend({}, this.state.formData);
    newData[name] = value;
    var isDirty = !_.isEqual(newData, this.state.initialData);
    this.setState({formData: newData, isDirty: isDirty});
  },

  handleFormSubmit: function (e) {
    e.preventDefault();

    this.getResource().save(this.state.formData, {wait: true})
                      .done(this.handleFormSuccess)
                      .error(this.handleFormError);
  },

  handleFormSuccess: function () {
    // Cleanup state
    this.clearValidation();
    this.setState({
      initialData: _.extend({}, this.state.formData),
      isDirty: false
    });

    _.isFunction(this.handleSuccess) && this.handleSuccess(this.getResource());
  },

  handleFormError: function (xhr) {
    this.validateResponse(xhr);

    _.isFunction(this.handleError) && this.handleError(xhr);
  }
};


module.exports = {
  FormValidationMixin: FormValidationMixin,
  ModelFormMixin: ModelFormMixin
};
