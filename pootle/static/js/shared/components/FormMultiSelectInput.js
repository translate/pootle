/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import Select from 'react-select';


const FormMultiSelectInput = React.createClass({

  propTypes: {
    multi: React.PropTypes.bool,
    clearAllText: React.PropTypes.string,
    clearValueText: React.PropTypes.string,
    handleChange: React.PropTypes.func.isRequired,
    name: React.PropTypes.string.isRequired,
    noResultsText: React.PropTypes.string,
    options: React.PropTypes.array.isRequired,
    placeholder: React.PropTypes.string,
    searchPromptText: React.PropTypes.string,
    value: React.PropTypes.array,
  },

  getDefaultProps() {
    return {
      multi: true,
      placeholder: gettext('Select...'),
      noResultsText: gettext('No results found'),
      clearValueText: gettext('Clear value'),
      clearAllText: gettext('Clear all'),
      searchPromptText: gettext('Type to search'),
    };
  },


  /* Handlers */

  handleChange(value) {
    this.props.handleChange(this.props.name, value.split(','));
  },


  /* Layout */

  render() {
    return (
      <Select
        onChange={this.handleChange}
        {...this.props}
      />
    );
  },

});


export default FormMultiSelectInput;
