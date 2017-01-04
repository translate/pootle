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


function createRow(item, index) {
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
          email={item.user.email}
          label={item.user.display_name}
          size={20}
          username={item.user.username}
        />
      </td>
      <td className="number">
        <span title={title}>{getScoreText(item.public_total_score)}</span>
      </td>
    </tr>
  );
}


const TopContributorsTable = ({ items }) => (
  <table className="top-scorers-table">
    <tbody>
      {items.map(createRow)}
    </tbody>
  </table>
);

TopContributorsTable.propTypes = {
  items: React.PropTypes.array.isRequired,
};


export default TopContributorsTable;
