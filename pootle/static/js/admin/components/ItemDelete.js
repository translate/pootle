/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';


const ItemDelete = React.createClass({

  propTypes: {
    item: React.PropTypes.object.isRequired,
    helpText: React.PropTypes.string,
    onDelete: React.PropTypes.func.isRequired,
  },


  /* Lifecycle */

  getInitialState() {
    return {
      buttonDisabled: true,
    };
  },


  /* Handlers */

  toggleButton() {
    this.setState({ buttonDisabled: !this.state.buttonDisabled });
  },

  handleClick(e) {
    e.preventDefault();
    this.props.item.destroy().then(this.props.onDelete);
  },

  render() {
    return (
      <div className="item-delete">
        <input
          type="checkbox"
          checked={!this.state.buttonDisabled}
          onChange={this.toggleButton}
        />
        <button
          className="btn btn-danger"
          disabled={this.state.buttonDisabled}
          onClick={this.handleClick}
        >{gettext('Delete')}</button>
      {this.props.helpText &&
        <span className="helptext">{this.props.helpText}</span>}
      </div>
    );
  },

});


export default ItemDelete;
