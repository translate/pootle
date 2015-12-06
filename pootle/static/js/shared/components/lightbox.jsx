/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import LayersMixin from 'mixins/layers';
import React from 'react';

import './lightbox.css';


const classNames = {
  lock: 'lightbox-lock',
};

const keys = {
  ESC: 27,
};


/* Reusable micro components */

const ModalHeader = React.createClass({

  render() {
    return (
      <div className="lightbox-header">
        {this.props.children}
      </div>
    );
  },

});


const ModalFooter = React.createClass({

  render() {
    return (
      <div className="lightbox-footer">
        {this.props.children}
      </div>
    );
  },

});


/* Actual components */

const ModalContainer = React.createClass({

  _previousFocus: null,
  _ownsLock: false,


  /* Lifecycle */

  componentWillMount() {
    this._previousFocus = document.activeElement;
  },

  componentDidMount() {
    if (!document.body.classList.contains(classNames.lock)) {
      this._ownsLock = true;
      document.body.classList.add(classNames.lock);
      document.addEventListener('keydown', this.handleKeyDown);
    }
  },

  componentWillUnmount() {
    if (this._ownsLock) {
      document.body.classList.remove(classNames.lock);
      document.removeEventListener('keydown', this.handleKeyDown);
    }
    this._previousFocus.focus();
  },


  /* Handlers */

  handleKeyDown(e) {
    if (e.keyCode === keys.ESC) {
      this.props.onClose();
    }
  },


  /* Layout */

  render() {
    return (
      <div className="lightbox-bg">
        <div className="lightbox-container">
          <div className={cx('lightbox-body', this.props.className)}
               style={this.props.style}
               tabIndex="-1">
            {this.props.children}
          </div>
        </div>
      </div>
    );
  },

});


export const Modal = React.createClass({
  mixins: [LayersMixin],

  propTypes: {
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
      <button className="lightbox-close"
              onClick={this.handleClose}>×</button>
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
    return null;
  },

});


export const Dialog = React.createClass({

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
        <button className="btn btn-primary"
                onClick={this.props.onAccept}>
          {this.props.okLabel}
        </button>
        <button className="btn"
                autoFocus={true}
                onClick={this.props.onCancel}>
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
