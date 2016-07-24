/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import FormCheckedInput from './FormCheckedInput';
import FormValueInput from './FormValueInput';
import FormSelectInput from './FormSelectInput';


const FormElement = React.createClass({

  propTypes: {
    type: React.PropTypes.string,
    label: React.PropTypes.string.isRequired,
    multiple: React.PropTypes.bool,
    name: React.PropTypes.string.isRequired,
    handleChange: React.PropTypes.func.isRequired,
    value: React.PropTypes.oneOfType([
      React.PropTypes.array,
      React.PropTypes.bool,
      React.PropTypes.number,
      React.PropTypes.string,
      React.PropTypes.array,
    ]).isRequired,
    help: React.PropTypes.string,
    errors: React.PropTypes.array,
  },

  /* Lifecycle */

  getDefaultProps() {
    return {
      type: 'text',
    };
  },


  /* Layout */

  render() {
    const { errors } = this.props;
    const fieldId = `id_${this.props.name}`;
    const hint = this.props.help;

    const InputComponent = {
      text: FormValueInput,
      email: FormValueInput,
      password: FormValueInput,
      textarea: FormValueInput,

      checkbox: FormCheckedInput,
      radio: FormCheckedInput,

      select: FormSelectInput,
    }[this.props.type];

    return (
      <div className="field-wrapper">
        <label htmlFor={fieldId}>{this.props.label}</label>
        <InputComponent id={fieldId} {...this.props} />
      {errors &&
        <ul className="errorlist">{errors.map((msg, i) => (
          <li key={i}>{msg}</li>
        ))}</ul>}
      {hint &&
        <span className="helptext">{hint}</span>}
      </div>
    );
  },

});


export default FormElement;
