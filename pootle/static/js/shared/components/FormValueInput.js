/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';


const FormValueInput = React.createClass({

  propTypes: {
    handleChange: React.PropTypes.func.isRequired,
    type: React.PropTypes.string,
    value: React.PropTypes.string,
  },

  handleChange(e) {
    this.props.handleChange(e.target.name, e.target.value);
  },


  render() {
    if (this.props.type === 'textarea') {
      return <textarea onChange={this.handleChange} {...this.props} />;
    }

    return <input onChange={this.handleChange} {...this.props} />;
  },

});


export default FormValueInput;
