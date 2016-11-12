/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';


const Score = React.createClass({

  propTypes: {
    value: React.PropTypes.number.isRequired,
  },

  render() {
    return (
       <span id="user-score">{this.props.value}</span>
    );
  },

});


export default Score;
