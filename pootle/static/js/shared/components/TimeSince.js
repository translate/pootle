/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React, { PropTypes } from 'react';
import { PureRenderMixin } from 'react-addons-pure-render-mixin';

// FIXME: avoid relative import
import { relativeDate } from '../../utils';


const TimeSince = React.createClass({

  propTypes: {
    dateTime: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
  },

  mixins: [PureRenderMixin],

  componentWillMount() {
    this.tickTimer = null;

    this.tick({ refresh: false });
  },

  componentWillReceiveProps(nextProps) {
    if (nextProps.dateTime !== this.props.dateTime) {
      this.cleanup();
    }
  },

  componentWillUnmount() {
    this.cleanup();
  },

  cleanup() {
    if (this.tickTimer !== null) {
      clearTimeout(this.tickTimer);
      this.tickTimer = null;
    }
  },

  tick(opts = { refresh: true }) {
    const past = Date.parse(this.props.dateTime);
    const now = Date.now();
    const seconds = Math.round(Math.abs(now - past) / 1000);

    let interval;

    if (seconds < 60) {
      interval = 1000 * 30;
    } else if (seconds < 60 * 60) {
      interval = 1000 * 60;
    } else if (seconds < 60 * 60 * 24) {
      interval = 1000 * 60 * 60;
    }

    if (interval !== undefined) {
      this.tickTimer = setTimeout(() => this.tick(), interval);
    }

    if (opts.refresh) {
      this.forceUpdate();
    }
  },

  render() {
    const displayTime = relativeDate(Date.parse(this.props.dateTime));

    return (
      <time
        className="extra-item-meta"
        title={this.props.title}
        dateTime={this.props.dateTime}
        {...this.props}
      >
        {displayTime}
      </time>
    );
  },

});


export default TimeSince;
