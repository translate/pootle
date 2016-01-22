/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React from 'react';


const ItemTableRow = React.createClass({

  propTypes: {
    fields: React.PropTypes.array.isRequired,
    item: React.PropTypes.object.isRequired,
    index: React.PropTypes.number.isRequired,
    selectedItem: React.PropTypes.object,
    onSelectItem: React.PropTypes.func.isRequired,
  },

  render() {
    const { item } = this.props;
    const { selectedItem } = this.props;
    const { index } = this.props;
    const values = item.toJSON();

    values.index = index + 1;
    function createColumn(field, i) {
      return <td key={i}>{values[field]}</td>;
    }

    const classNames = cx({
      'is-selected': selectedItem && item.id === selectedItem.id,
      // FIXME: this is too coupled to certain item types
      'is-disabled': item.get('disabled'),
      'row-divider': index !== 0 && index % 10 === 0,
    });

    return (
      <tr
        className={classNames}
        key={item.id}
        onClick={() => this.props.onSelectItem(item.id)}
      >
        {this.props.fields.map(createColumn)}
      </tr>
    );
  },

});


export default ItemTableRow;
