/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React, { PropTypes } from 'react';
import { PureRenderMixin } from 'react/addons';


const TimeSince = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    dateTime: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
  },

  render() {
    return (
      <time
        className="extra-item-meta js-relative-date"
        title={this.props.title}
        dateTime={this.props.dateTime}
      >
        {this.props.title}
      </time>
    );
  }

});


export default TimeSince;
