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
    name: React.PropTypes.string.isRequired,
    value: React.PropTypes.string.isRequired,
    options: React.PropTypes.array.isRequired,
    handleChange: React.PropTypes.func.isRequired,
  },


  /* Handlers */

  handleChange(value) {
    this.props.handleChange(this.props.name, value);
  },


  /* Layout */

  render() {
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


export default FormSelectInput;
