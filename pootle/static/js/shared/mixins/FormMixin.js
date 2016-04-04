/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import _ from 'underscore';

import FormValidationMixin from './FormValidationMixin';

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
    this.setState({ isDirty, formData: newData });
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


export default FormMixin;
