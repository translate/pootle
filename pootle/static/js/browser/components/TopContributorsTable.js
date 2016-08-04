/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import Avatar from 'components/Avatar';
import { t } from 'utils/i18n';


function getScoreText(score) {
  if (score > 0) {
    return t('+%(score)s', { score });
  }
  return score;
}


const TopContributorsTable = React.createClass({

  propTypes: {
    items: React.PropTypes.array.isRequired,
    hasMoreItems: React.PropTypes.bool.isRequired,
    loadMore: React.PropTypes.func.isRequired,
  },

  createRow(item, index) {
    const title = (`
      <span class="value">${item.suggested}</span> suggested<br/>
      <span class="value">${item.translated}</span> translated<br/>
      <span class="value">${item.reviewed}</span> reviewed<br/>
    `);
    return (
      <tr key={`top-contibutor-${index}`}>
        <td className="number">{t('#%(position)s', { position: index + 1 })}</td>
        <td className="user top-scorer">
          <Avatar
            email={item.email}
            label={item.display_name}
            size={20}
            username={item.username}
          />
        </td>
        <td className="number">
          <span title={title}>{getScoreText(item.public_total_score)}</span>
        </td>
      </tr>
    );
  },

  render() {
    let loadMore;

    if (this.props.hasMoreItems) {
      loadMore = (
        <div className="more-top-contributors">
          <a onClick={this.props.loadMore}>
            <span className="show-more">{gettext('More...')}</span>
          </a>
        </div>
      );
    }
    return (
      <div className="bd">
        <table className="top-scorers-table">
          <tbody>
            {this.props.items.map(this.createRow)}
          </tbody>
        </table>
        {loadMore}
      </div>
    );
  },

});


export default TopContributorsTable;
