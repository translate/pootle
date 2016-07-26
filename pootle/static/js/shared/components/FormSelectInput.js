/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import Select from 'react-select';


const FormSelectInput = React.createClass({

  propTypes: {
    clearAllText: React.PropTypes.string,
    clearValueText: React.PropTypes.string,
    handleChange: React.PropTypes.func.isRequired,
    multiple: React.PropTypes.bool,
    name: React.PropTypes.string.isRequired,
    noResultsText: React.PropTypes.string,
    options: React.PropTypes.array.isRequired,
    placeholder: React.PropTypes.string,
    searchPromptText: React.PropTypes.string,
    value: React.PropTypes.oneOfType([
      React.PropTypes.array,
      React.PropTypes.number,
      React.PropTypes.string,
    ]).isRequired,
  },

  getDefaultProps() {
    return {
      multiple: false,
      placeholder: gettext('Select...'),
      noResultsText: gettext('No results found'),
      clearValueText: gettext('Clear value'),
      clearAllText: gettext('Clear all'),
      searchPromptText: gettext('Type to search'),
    };
  },


  /* Handlers */

  handleChange(value) {
    const newValue = this.props.multiple ? value.split(',') : value;
    this.props.handleChange(this.props.name, newValue);
  },


  /* Layout */

  render() {
    const { value } = this.props;
    /* FIXME: react-select#25 prevents using non-string values */
    const selectValue = this.props.multiple ? value : value.toString();
    return (
      <Select
        onChange={this.handleChange}
        {...this.props}
        multi={this.props.multiple}
        value={selectValue}
      />
    );
  },

});


export default FormSelectInput;
