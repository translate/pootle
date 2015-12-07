/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';


const ContentPreview = React.createClass({

  propTypes: {
    value: React.PropTypes.string.isRequired,

    style: React.PropTypes.object,
  },

  render() {
    return (
      <div
        className="content-preview"
        style={this.props.style}
      >
        {this.props.value ?
          <div
            className="staticpage"
            dangerouslySetInnerHTML={{ __html: this.props.value }}
          /> :
          <div className="placeholder">
            {gettext('Preview will be displayed here.')}
          </div>
        }
      </div>
    );
  },

});


export default ContentPreview;
