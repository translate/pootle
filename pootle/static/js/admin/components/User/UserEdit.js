/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import UserForm from './UserForm';


const UserEdit = React.createClass({

  propTypes: {
    collection: React.PropTypes.object.isRequired,
    model: React.PropTypes.object,
    onAdd: React.PropTypes.func.isRequired,
    onDelete: React.PropTypes.func.isRequired,
    onSuccess: React.PropTypes.func.isRequired,
  },

  render() {
    return (
      <div className="item-edit">
        <div className="hd">
          <h2>{gettext('Edit User')}</h2>
          <button
            onClick={this.props.onAdd}
            className="btn btn-primary"
          >
          {gettext('Add User')}
          </button>
        </div>
        <div className="bd">
        {!this.props.model ?
          <p>{gettext('Use the search form to find the user, then click on a user to edit.')}</p> :
          <UserForm
            key={this.props.model.id}
            model={this.props.model}
            collection={this.props.collection}
            onSuccess={this.props.onSuccess}
            onDelete={this.props.onDelete}
          />
        }
        </div>
      </div>
    );
  },

});


export default UserEdit;
