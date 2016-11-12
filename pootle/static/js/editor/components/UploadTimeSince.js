/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React, { PropTypes } from 'react';
import { PureRenderMixin } from 'react-addons-pure-render-mixin';

import TimeSince from 'components/TimeSince';
import { tct } from 'utils/i18n';

const UploadTimeSince = React.createClass({

  propTypes: {
    dateTime: PropTypes.string.isRequired,
    relativeTime: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
  },

  mixins: [PureRenderMixin],

  render() {
    const timeSince = (
      <TimeSince
        className=""
        {...this.props}
      />
    );

    return (
      <span className="extra-item-meta">
        {tct('%(timeSince)s via file upload', { timeSince })}
      </span>
    );
  },

});


export default UploadTimeSince;
