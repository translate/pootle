/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import LayeredComponent from './LayeredComponent';
import ModalContainer from './ModalContainer';


export const ModalHeader = ({ children }) => (
  <div className="lightbox-header">
    {children}
  </div>
);

ModalHeader.propTypes = {
  children: React.PropTypes.node.isRequired,
};


export const ModalFooter = ({ children }) => (
  <div className="lightbox-footer">
    {children}
  </div>
);

ModalFooter.propTypes = {
  children: React.PropTypes.node.isRequired,
};


const Modal = React.createClass({

  propTypes: {
    children: React.PropTypes.node.isRequired,
    title: React.PropTypes.string,
    showClose: React.PropTypes.bool,
    onClose: React.PropTypes.func.isRequired,
    header: React.PropTypes.func,
    footer: React.PropTypes.func,
  },

  /* Lifecycle */

  getDefaultProps() {
    return {
      title: '',
      showClose: true,
    };
  },


  /* Handlers */

  handleClose() {
    // Parent components need to take care of rendering the component
    // and unmounting it according to their needs
    this.props.onClose();
  },


  /* Layout */

  renderHeader() {
    if (this.props.header) {
      return (
        <ModalHeader>
          {this.props.header()}
        </ModalHeader>
      );
    }

    const title = (this.props.title &&
      <h3 className="lightbox-title">{this.props.title}</h3>
    );
    const closeBtn = (this.props.showClose &&
      <button
        className="lightbox-close"
        onClick={this.handleClose}
      >×</button>
    );

    return (
      <ModalHeader>
        {title}
        {closeBtn}
      </ModalHeader>
    );
  },

  renderFooter() {
    if (this.props.footer) {
      return (
        <ModalFooter>
          {this.props.footer()}
        </ModalFooter>
      );
    }

    return null;
  },

  renderLayer() {
    return (
      <ModalContainer {...this.props}>
        {this.renderHeader()}
        <div className="lightbox-content">
          {this.props.children}
        </div>
        {this.renderFooter()}
      </ModalContainer>
    );
  },

  render() {
    return (
      <LayeredComponent>
        {this.renderLayer()}
      </LayeredComponent>
    );
  },

});


export default Modal;
