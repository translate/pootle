/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import StatsAPI from 'api/StatsAPI';
import TopContributors from './TopContributors';


const Stats = React.createClass({

  propTypes: {
    topContributors: React.PropTypes.array.isRequired,
    hasMoreContributors: React.PropTypes.bool.isRequired,
    pootlePath: React.PropTypes.string.isRequired,
  },

  getInitialState() {
    return {
      topContributors: this.props.topContributors,
      hasMoreContributors: this.props.hasMoreContributors,
    };
  },

  onLoadMoreTopContributors(data) {
    const topContributors = this.state.topContributors.concat(data.items);
    this.setState({
      topContributors,
      hasMoreContributors: data.has_more_items,
    });
  },

  loadMoreTopContributors() {
    if (!this.state.hasMoreContributors) {
      return false;
    }
    const params = { offset: this.state.topContributors.length };
    return StatsAPI.getTopContributors(this.props.pootlePath, params)
      .done(this.onLoadMoreTopContributors);
  },

  render() {
    return (
      <TopContributors
        items={this.state.topContributors}
        hasMoreItems={this.state.hasMoreContributors}
        loadMore={this.loadMoreTopContributors}
      />
    );
  },

});


export default Stats;
