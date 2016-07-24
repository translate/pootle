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
    handleChange: React.PropTypes.func.isRequired,
    multiple: React.PropTypes.bool,
    name: React.PropTypes.string.isRequired,
    options: React.PropTypes.array.isRequired,
    value: React.PropTypes.oneOfType([
      React.PropTypes.array,
      React.PropTypes.number,
      React.PropTypes.string,
      React.PropTypes.array,
    ]).isRequired,
  },

  handleChange(value) {
    const newValue = this.props.multiple ? value.split(',') : value;
    this.props.handleChange(this.props.name, newValue);
  },

  render() {
    const { value } = this.props;
    /* FIXME: react-select#25 prevents using non-string values */
    const selectValue = this.props.multiple ? value : value.toString();
    return (
      <Select
        clearAllText={gettext('Clear all')}
        clearValueText={gettext('Clear value')}
        noResultsText={gettext('No results found')}
        onChange={this.handleChange}
        placeholder={gettext('Select...')}
        searchPromptText={gettext('Type to search')}
        {...this.props}
        multi={this.props.multiple}
        value={selectValue}
      />
    );
  },

});


export default FormSelectInput;
