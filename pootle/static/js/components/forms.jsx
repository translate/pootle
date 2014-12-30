'use strict';

var React = require('react/addons');
var _ = require('underscore');


var FormElement = React.createClass({


  /* Layout */

  render: function () {
    var attribute = this.props.attribute;
    var fieldId = ['id', attribute].join('_');
    var hint = this.props.help;

    var errors = (_.size(this.props.errors) > 0 &&
                  this.props.errors[attribute]);

    var type = this.props.type || 'text';  // Default to `text` type
    var el = {
      text: <FormValueInput />,
      email: <FormValueInput />,
      password: <FormValueInput />,
      textarea: <FormValueInput />,

      checkbox: <FormCheckedInput />,
      radio: <FormCheckedInput />

      // TODO: FormSelectInput
    }[type];

    var newProps = {
      id: fieldId,
      name: attribute,
      value: this.props.formData[attribute],
      handleChange: this.props.handleChange,
      placeholder: this.props.placeholder,
      autoFocus: this.props.autoFocus,
      readOnly: this.props.readOnly,
      type: type
    };
    var formInput = React.addons.cloneWithProps(el, newProps);

    return (
      <div className="field-wrapper">
        <label htmlFor={fieldId}>{this.props.label}</label>
        {formInput}
      {hint &&
        <span className="helptext">{hint}</span>}
      {errors &&
        <ul className="errorlist">{errors.map(function (msg, i) {
          return <li key={i}>{msg}</li>;
        })}</ul>}
      </div>
    );
  }
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
  }

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
  }

});


module.exports = {
  FormElement: FormElement
};
