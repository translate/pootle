/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React from 'react';


const ItemTable = React.createClass({

  propTypes: {
    fields: React.PropTypes.array.isRequired,
    items: React.PropTypes.object.isRequired,
    resultsCaption: React.PropTypes.string.isRequired,
    selectedItem: React.PropTypes.object,
    onSelectItem: React.PropTypes.func.isRequired,
  },

  render() {
    let createRow = function (item, index) {
      return (
        <ItemTableRow
          fields={this.props.fields}
          key={item.id}
          item={item}
          index={index}
          selectedItem={this.props.selectedItem}
          onSelectItem={this.props.onSelectItem} />
        );
      };

    return (
      <table>
        <caption>{this.props.resultsCaption}</caption>
        <tbody>
        {this.props.items.map(createRow.bind(this))}
        </tbody>
      </table>
    );
  }

});


const ItemTableRow = React.createClass({

  propTypes: {
    fields: React.PropTypes.array.isRequired,
    item: React.PropTypes.object.isRequired,
    index: React.PropTypes.number.isRequired,
    selectedItem: React.PropTypes.object,
    onSelectItem: React.PropTypes.func.isRequired,
  },

  render() {
    let { item } = this.props;
    let { selectedItem } = this.props;
    let { index } = this.props;
    let values = item.toJSON();

    values.index = index + 1;
    let createColumn = function (field, i) {
      return <td key={i}>{values[field]}</td>;
    };

    let classNames = cx({
      'is-selected': selectedItem && item.id === selectedItem.id,
      // FIXME: this is too coupled to certain item types
      'is-disabled': item.get('disabled'),
      'row-divider': index !== 0 && index % 10 === 0,
    });

    return (
      <tr className={classNames}
          key={item.id}
          onClick={this.props.onSelectItem.bind(null, item)}>
        {this.props.fields.map(createColumn)}
      </tr>
    );
  },

});


export default ItemTable;
