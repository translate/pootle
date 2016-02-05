/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React from 'react';

import tabInScope from 'utils/tabInScope';

import './lightbox.css';


const classNames = {
  lock: 'lightbox-lock',
};

const keys = {
  ESC: 27,
  TAB: 9,
};


const ModalContainer = React.createClass({

  propTypes: {
    children: React.PropTypes.node.isRequired,
    onClose: React.PropTypes.func.isRequired,
    className: React.PropTypes.string,
    style: React.PropTypes.object,
  },

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

  _previousFocus: null,
  _ownsLock: false,


  /* Handlers */

  handleKeyDown(e) {
    if (e.keyCode === keys.TAB) {
      tabInScope(this.refs.body, e);
    }
    if (e.keyCode === keys.ESC) {
      this.props.onClose();
    }
  },


  /* Layout */

  render() {
    return (
      <div className="lightbox-bg">
        <div className="lightbox-container">
          <div
            className={cx('lightbox-body', this.props.className)}
            ref="body"
            style={this.props.style}
            tabIndex="-1"
          >
            {this.props.children}
          </div>
        </div>
      </div>
    );
  },

});


export default ModalContainer;
