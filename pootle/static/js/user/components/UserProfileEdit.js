/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import Backbone from 'backbone';
import React from 'react';

import { Dialog, Modal } from 'components/lightbox';

import { UserProfileForm } from '../forms';


const UserProfileEdit = React.createClass({

  /* Lifecycle */

  getInitialState() {
    return {
      editing: false,
      confirmClose: false,
      isDirty: false
    };
  },

  setupRoutes(router) {
    router.on('route:main', (qs) => {
      this.setState({editing: false});
    });

    router.on('route:edit', (id, qs) => {
      this.setState({editing: true});
    });
  },

  componentWillMount() {
    this.setupRoutes(this.props.router);
    Backbone.history.start({pushState: true, root: this.props.appRoot});
  },

  componentWillUpdate(nextProps, nextState) {
    this.handleURL(nextState);
  },


  /* State-changing handlers */

  handleEdit() {
    this.setState({editing: true});
  },

  handleClose(opts) {
    opts = opts || {};
    let forceClose = opts.forceClose || false;

    if (this.state.isDirty && !forceClose) {
      this.setState({confirmClose: true});
    } else {
      this.setState({
        editing: false,
        confirmClose: false,
        isDirty: false
      });
    }
  },

  handleSave(item) {
    this.handleClose();
    window.location.reload();
  },

  handleDlgOk() {
    this.handleClose({forceClose: true});
  },

  handleDlgCancel() {
    this.setState({confirmClose: false});
  },

  handleDirtyFlag(isDirty) {
    this.setState({isDirty: isDirty});
  },


  /* Handlers */

  handleURL(newState) {
    let newURL = newState.editing ? '/edit/' : '/';
    this.props.router.navigate(newURL);
  },


  /* Layout */

  render() {
    return (
      <div>
        <div className="edit-profile-btn">
          <button className="btn btn-primary"
                  onClick={this.handleEdit}>
            {gettext('Edit My Public Profile')}
          </button>
        </div>
      {this.state.editing &&
        <Modal
          className="user-edit"
          onClose={this.handleClose}
          title={gettext('My Public Profile')}>
          <div id="user-edit">
            <UserProfileForm model={this.props.user}
                             onDirty={this.handleDirtyFlag}
                             onSuccess={this.handleSave} />
          </div>
        </Modal>}
      {this.state.confirmClose &&
        <Dialog
          onAccept={this.handleDlgOk}
          onCancel={this.handleDlgCancel}
          onClose={this.handleDlgCancel}
          title={gettext('Discard changes.')}
          okLabel={gettext('Yes')}
          cancelLabel={gettext('No')}>
          {gettext('There are unsaved changes. Do you want to discard them?')}
        </Dialog>}
      </div>
    );
  }

});


export default UserProfileEdit;
