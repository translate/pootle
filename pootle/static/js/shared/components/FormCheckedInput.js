/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';


const FormCheckedInput = React.createClass({

  handleChange(e) {
    this.props.handleChange(e.target.name, e.target.checked);
  },


  render() {
    return (
      <input
        checked={this.props.value}
        onChange={this.handleChange}
        {...this.props}
      />
    );
  },

});


export default FormCheckedInput;
