/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';


const ModalHeader = React.createClass({

  propTypes: {
    children: React.PropTypes.node.isRequired,
  },

  render() {
    return (
      <div className="lightbox-header">
        {this.props.children}
      </div>
    );
  },

});


export default ModalHeader;
