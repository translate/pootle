/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import cx from 'classnames';

var React = require('react');

var LayersMixin = require('mixins/layers');

require('./lightbox.css');


var classNames = {
  lock: 'lightbox-lock',
};

var keys = {
  ESC: 27,
};


/* Reusable micro components */

var ModalHeader = React.createClass({

  render: function () {
    return (
      <div className="lightbox-header">
        {this.props.children}
      </div>
    );
  },

});


var ModalFooter = React.createClass({

  render: function () {
    return (
      <div className="lightbox-footer">
        {this.props.children}
      </div>
    );
  },

});


/* Actual components */

var ModalContainer = React.createClass({

  _previousFocus: null,
  _ownsLock: false,


  /* Lifecycle */

  componentWillMount: function () {
    this._previousFocus = document.activeElement;
  },

  componentDidMount: function () {
    if (!document.body.classList.contains(classNames.lock)) {
      this._ownsLock = true;
      document.body.classList.add(classNames.lock);
      document.addEventListener('keydown', this.handleKeyDown);
    }
  },

  componentWillUnmount: function () {
    if (this._ownsLock) {
      document.body.classList.remove(classNames.lock);
      document.removeEventListener('keydown', this.handleKeyDown);
    }
    this._previousFocus.focus();
  },


  /* Handlers */

  handleKeyDown: function (e) {
    if (e.keyCode === keys.ESC) {
      this.props.onClose();
    }
  },


  /* Layout */

  render: function () {
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


var Modal = React.createClass({
  mixins: [LayersMixin],

  propTypes: {
    title: React.PropTypes.string,
    showClose: React.PropTypes.bool,
    onClose: React.PropTypes.func.isRequired,
    header: React.PropTypes.func,
    footer: React.PropTypes.func,
  },


  /* Lifecycle */

  getDefaultProps: function () {
    return {
      title: '',
      showClose: true,
    };
  },


  /* Handlers */

  handleClose: function () {
    // Parent components need to take care of rendering the component
    // and unmounting it according to their needs
    this.props.onClose();
  },


  /* Layout */

  renderHeader: function () {
    if (this.props.header) {
      return (
        <ModalHeader>
          {this.props.header()}
        </ModalHeader>
      );
    }

    var title = (this.props.title &&
      <h3 className="lightbox-title">{this.props.title}</h3>
    );
    var closeBtn = (this.props.showClose &&
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

  renderFooter: function () {
    if (this.props.footer) {
      return (
        <ModalFooter>
          {this.props.footer()}
        </ModalFooter>
      );
    }

    return null;
  },

  renderLayer: function () {
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

  render: function () {
    return null;
  },

});


var Dialog = React.createClass({

  propTypes: {
    okLabel: React.PropTypes.string,
    cancelLabel: React.PropTypes.string,
    onAccept: React.PropTypes.func.isRequired,
    onCancel: React.PropTypes.func.isRequired,
    header: React.PropTypes.func,
    footer: React.PropTypes.func,
  },


  /* Lifecycle */

  getDefaultProps: function () {
    return {
      okLabel: 'OK',
      cancelLabel: 'Cancel',
    };
  },


  /* Layout */

  renderFooter: function () {
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

  render: function () {
    return (
      <Modal {...this.props} footer={this.renderFooter} />
    );
  },

});


module.exports = {
  Modal: Modal,
  Dialog: Dialog,
};
