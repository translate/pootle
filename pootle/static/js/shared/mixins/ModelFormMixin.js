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
import FormMixin from './FormMixin';


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

    this.getResource().save(this.state.formData, { wait: true })
                      .done(this.handleFormSuccess)
                      .error(this.handleFormError);
  },

};


export default ModelFormMixin;
