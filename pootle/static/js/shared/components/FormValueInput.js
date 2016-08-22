/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import AutosizeTextarea from './AutosizeTextarea';


const FormValueInput = React.createClass({

  propTypes: {
    handleChange: React.PropTypes.func.isRequired,
    autosize: React.PropTypes.bool,
    type: React.PropTypes.string,
    value: React.PropTypes.string,
  },

  getDefaultProps() {
    return {
      autosize: true,
    };
  },

  handleChange(e) {
    this.props.handleChange(e.target.name, e.target.value);
  },


  render() {
    if (this.props.type === 'textarea') {
      if (this.props.autosize) {
        return (
          <AutosizeTextarea
            onChange={this.handleChange}
            {...this.props}
          />
        );
      }

      return (
        <textarea
          onChange={this.handleChange}
          {...this.props}
        />
      );
    }

    return <input onChange={this.handleChange} {...this.props} />;
  },

});


export default FormValueInput;
