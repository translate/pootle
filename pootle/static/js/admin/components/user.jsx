'use strict';

var React = require('react');

var UserForm = require('../forms').UserForm;


var UserAdd = React.createClass({

  /* Layout */

  render: function () {
    return (
      <div className="item-add">
        <div className="hd">
          <h2>{gettext('Add User')}</h2>
          <button
            onClick={this.props.handleCancel}
            className="btn btn-primary">{gettext('Cancel')}</button>
        </div>
        <div className="bd">
          <UserForm
            model={new this.props.model()}
            collection={this.props.collection}
            handleSuccess={this.props.handleSuccess} />
        </div>
      </div>
    );
  }

});


var UserEdit = React.createClass({

  /* Layout */

  render: function () {
    return (
      <div className="item-edit">
        <div className="hd">
          <h2>{gettext('Edit User')}</h2>
          <button
            onClick={this.props.handleAdd}
            className="btn btn-primary">{gettext('Add User')}</button>
        </div>
        <div className="bd">
        {!this.props.model ?
          <p>{gettext('Use the search form to find the user, then click on a user to edit.')}</p> :
          <UserForm
            key={this.props.model.id}
            model={this.props.model}
            collection={this.props.collection}
            handleSuccess={this.props.handleSuccess}
            handleDelete={this.props.handleDelete} />
        }
        </div>
      </div>
    );
  }

});


module.exports = {
  UserAdd: UserAdd,
  UserEdit: UserEdit
};
