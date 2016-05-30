/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import Modal, { ModalFooter } from './Modal';


const Dialog = React.createClass({

  propTypes: {
    okLabel: React.PropTypes.string,
    cancelLabel: React.PropTypes.string,
    onAccept: React.PropTypes.func.isRequired,
    onCancel: React.PropTypes.func.isRequired,
    header: React.PropTypes.func,
    footer: React.PropTypes.func,
  },


  /* Lifecycle */

  getDefaultProps() {
    return {
      okLabel: 'OK',
      cancelLabel: 'Cancel',
    };
  },


  /* Layout */

  renderFooter() {
    return (
      <ModalFooter>
        <button
          className="btn btn-primary"
          onClick={this.props.onAccept}
        >
          {this.props.okLabel}
        </button>
        <button
          className="btn"
          autoFocus
          onClick={this.props.onCancel}
        >
          {this.props.cancelLabel}
        </button>
      </ModalFooter>
    );
  },

  render() {
    return (
      <Modal {...this.props} footer={this.renderFooter} />
    );
  },

});


export default Dialog;
