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

var Select = require('react-select');


var FormElement = React.createClass({

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

  getDefaultProps: function () {
    return {
      type: 'text',
    };
  },


  /* Layout */

  render: function () {
    var attribute = this.props.attribute;
    var fieldId = ['id', attribute].join('_');
    var hint = this.props.help;

    var errors = (_.size(this.props.errors) > 0 &&
                  this.props.errors[attribute]);

    var inputClass = {
      text: FormValueInput,
      email: FormValueInput,
      password: FormValueInput,
      textarea: FormValueInput,

      checkbox: FormCheckedInput,
      radio: FormCheckedInput,

      select: FormSelectInput,
    }[this.props.type];

    var newProps = {
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

    var inputProps = _.extend({}, this.props, newProps);
    var formInput = React.createFactory(inputClass)(inputProps);

    return (
      <div className="field-wrapper">
        <label htmlFor={fieldId}>{this.props.label}</label>
        {formInput}
      {errors &&
        <ul className="errorlist">{errors.map(function (msg, i) {
          return <li key={i}>{msg}</li>;
        })}</ul>}
      {hint &&
        <span className="helptext">{hint}</span>}
      </div>
    );
  },

});


var FormValueInput = React.createClass({

  /* Handlers */

  handleChange: function (e) {
    this.props.handleChange(e.target.name, e.target.value);
  },


  /* Layout */

  render: function () {
    if (this.props.type === 'textarea') {
      return <textarea onChange={this.handleChange} {...this.props} />;
    }

    return <input onChange={this.handleChange} {...this.props} />;
  },

});


var FormCheckedInput = React.createClass({

  /* Handlers */

  handleChange: function (e) {
    this.props.handleChange(e.target.name, e.target.checked);
  },


  /* Layout */

  render: function () {
    return <input checked={this.props.value} onChange={this.handleChange}
                  {...this.props} />;
  },

});


var FormSelectInput = React.createClass({

  propTypes: {
    name: React.PropTypes.string.isRequired,
    value: React.PropTypes.string.isRequired,
    options: React.PropTypes.array.isRequired,
    handleChange: React.PropTypes.func.isRequired,
  },


  /* Handlers */

  handleChange: function (value, values) {
    this.props.handleChange(this.props.name, value);
  },


  /* Layout */

  render: function () {
    return (
      <Select
        value={this.props.value.toString()}
        options={this.props.options}
        onChange={this.handleChange}
        {...this.props}
      />
    );
  },

});


module.exports = {
  FormElement: FormElement,
};
