/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import StatsAPI from 'api/StatsAPI';
import { t } from 'utils/i18n';

import TopContributorsTable from './TopContributorsTable';


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
    const params = { offset: this.state.topContributors.length };
    return StatsAPI.getTopContributors(this.props.pootlePath, params)
      .done(this.onLoadMoreTopContributors);
  },

  renderLoadMoreButton() {
    if (!this.state.hasMoreContributors) {
      return null;
    }

    return (
      <div className="more-top-contributors">
        <a onClick={this.loadMoreTopContributors}>
          <span className="show-more">{t('More...')}</span>
        </a>
      </div>
    );
  },

  render() {
    if (!this.state.topContributors.length) {
      return null;
    }

    return (
      <div className="summary-2-col">
        <h3 className="top">{t('Contributors, 30 Days')}</h3>
        <div className="bd">
          <TopContributorsTable
            items={this.state.topContributors}
          />
          {this.renderLoadMoreButton()}
        </div>
      </div>
    );
  },

});


export default Stats;
