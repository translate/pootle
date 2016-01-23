/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import OdometerLib from 'odometer';
import React from 'react';


const Odometer = React.createClass({

  propTypes: {
    value: React.PropTypes.number.isRequired,
  },

  componentDidMount() {
    this.odometer = new OdometerLib({
      el: this.refs.odometer,
      value: this.props.value,
    });
  },

  componentDidUpdate() {
    this.odometer.update(this.props.value);
  },

  render() {
    return (
      <div className="odometer" ref="odometer"></div>
    );
  },

});


export default Odometer;
