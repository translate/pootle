/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import React, { PropTypes } from 'react';


const TextToggle = React.createClass({

  propTypes: {
    defaultChecked: PropTypes.bool,
    labelActive: PropTypes.string,
    labelInactive: PropTypes.string,
    onClick: PropTypes.func,
    style: PropTypes.object,
  },

  getDefaultProps() {
    return {
      defaultChecked: false,
      labelActive: 'Active',
      labelInactive: 'Inactive',
    };
  },

  getInitialState() {
    return {
      isActive: this.props.defaultChecked,
    };
  },

  handleClick() {
    this.setState({ isActive: !this.state.isActive });
    if (this.props.onClick) {
      this.props.onClick({ isActive: this.state.isActive });
    }
  },

  render() {
    const label = this.state.isActive ?
      this.props.labelActive : this.props.labelInactive;
    const style = assign({}, { cursor: 'pointer' }, this.props.style);

    return (
      <span
        onClick={this.handleClick}
        style={style}
      >
        {label}
      </span>
    );
  },

});


export default TextToggle;
