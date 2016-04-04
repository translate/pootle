/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import Dialog from 'components/Dialog';
import Modal from 'components/Modal';

import UserProfileForm from './UserProfileForm';


const UserProfileEdit = React.createClass({

  propTypes: {
    appRoot: React.PropTypes.string.isRequired,
    user: React.PropTypes.object.isRequired,
  },

  /* Lifecycle */

  getInitialState() {
    return {
      editing: /\/edit\/?$/.test(window.location),
      confirmClose: false,
      isDirty: false,
    };
  },

  componentWillUpdate(nextProps, nextState) {
    this.handleURL(nextState);
  },

  /* State-changing handlers */

  handleEdit() {
    this.setState({ editing: true });
  },

  handleClose(opts = { forceClose: false }) {
    const { forceClose } = opts;

    if (this.state.isDirty && !forceClose) {
      this.setState({ confirmClose: true });
    } else {
      this.setState({
        editing: false,
        confirmClose: false,
        isDirty: false,
      });
    }
  },

  handleSave() {
    this.handleClose();
    window.location.reload();
  },

  handleDlgOk() {
    this.handleClose({ forceClose: true });
  },

  handleDlgCancel() {
    this.setState({ confirmClose: false });
  },

  handleDirtyFlag(isDirty) {
    this.setState({ isDirty });
  },


  /* Handlers */

  handleURL(newState) {
    const { appRoot } = this.props;
    const newURL = newState.editing ? `${appRoot}edit/` : appRoot;
    window.history.pushState({}, '', newURL);
  },


  /* Layout */

  render() {
    return (
      <div>
        <div className="edit-profile-btn">
          <button
            className="btn btn-primary"
            onClick={this.handleEdit}
          >
            {gettext('Edit My Public Profile')}
          </button>
        </div>
      {this.state.editing &&
        <Modal
          className="user-edit"
          onClose={this.handleClose}
          title={gettext('My Public Profile')}
        >
          <div id="user-edit">
            <UserProfileForm
              model={this.props.user}
              onDirty={this.handleDirtyFlag}
              onSuccess={this.handleSave}
            />
          </div>
        </Modal>}
      {this.state.confirmClose &&
        <Dialog
          onAccept={this.handleDlgOk}
          onCancel={this.handleDlgCancel}
          onClose={this.handleDlgCancel}
          title={gettext('Discard changes.')}
          okLabel={gettext('Yes')}
          cancelLabel={gettext('No')}
        >
          {gettext('There are unsaved changes. Do you want to discard them?')}
        </Dialog>}
      </div>
    );
  },

});


export default UserProfileEdit;
