/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import ItemTableRow from './ItemTableRow';


const ItemTable = React.createClass({

  propTypes: {
    fields: React.PropTypes.array.isRequired,
    items: React.PropTypes.object.isRequired,
    resultsCaption: React.PropTypes.string.isRequired,
    selectedItem: React.PropTypes.object,
    onSelectItem: React.PropTypes.func.isRequired,
  },

  render() {
    function createRow(item, index) {
      return (
        <ItemTableRow
          fields={this.props.fields}
          key={item.id}
          item={item}
          index={index}
          selectedItem={this.props.selectedItem}
          onSelectItem={this.props.onSelectItem}
        />
        );
    }

    return (
      <table>
        <caption>{this.props.resultsCaption}</caption>
        <tbody>
        {this.props.items.map(createRow.bind(this))}
        </tbody>
      </table>
    );
  },

});


export default ItemTable;
