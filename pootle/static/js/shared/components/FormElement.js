/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import _ from 'underscore';

import FormCheckedInput from './FormCheckedInput';
import FormValueInput from './FormValueInput';
import FormSelectInput from './FormSelectInput';


const FormElement = React.createClass({

  propTypes: {
    type: React.PropTypes.string,
    attribute: React.PropTypes.string.isRequired,
    label: React.PropTypes.string.isRequired,
    handleChange: React.PropTypes.func.isRequired,
    formData: React.PropTypes.object.isRequired,
    help: React.PropTypes.string,
    errors: React.PropTypes.object,
  },

  /* Lifecycle */

  getDefaultProps() {
    return {
      type: 'text',
    };
  },


  /* Layout */

  render() {
    const { attribute } = this.props;
    const fieldId = `id_${attribute}`;
    const hint = this.props.help;

    const errors = (_.size(this.props.errors) > 0 &&
                    this.props.errors[attribute]);

    const inputClass = {
      text: FormValueInput,
      email: FormValueInput,
      password: FormValueInput,
      textarea: FormValueInput,

      checkbox: FormCheckedInput,
      radio: FormCheckedInput,

      select: FormSelectInput,
    }[this.props.type];

    const newProps = {
      id: fieldId,
      name: attribute,
      value: this.props.formData[attribute],
    };
    if (this.props.type === 'select') {
      // FIXME: react-select's issue #25 prevents using non-string values
      newProps.value = newProps.value.toString();

      newProps.placeholder = gettext('Select...');
      newProps.noResultsText = gettext('No results found');
      newProps.clearValueText = gettext('Clear value');
      newProps.clearAllText = gettext('Clear all');
      newProps.searchPromptText = gettext('Type to search');
    }

    const inputProps = _.extend({}, this.props, newProps);
    const formInput = React.createFactory(inputClass)(inputProps);

    return (
      <div className="field-wrapper">
        <label htmlFor={fieldId}>{this.props.label}</label>
        {formInput}
      {errors &&
        <ul className="errorlist">{errors.map((msg, i) => {
          return <li key={i}>{msg}</li>;
        })}</ul>}
      {hint &&
        <span className="helptext">{hint}</span>}
      </div>
    );
  },

});


export default FormElement;
