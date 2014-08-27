'use strict';

var Backbone = require('backbone');
var React = require('react');
var _ = require('underscore');

var Modal = require('../../components/lightbox').Modal;
var UserProfileForm = require('../forms').UserProfileForm;


var UserProfileEdit = React.createClass({

  /* Lifecycle */

  getInitialState: function () {
    return {
      editing: false
    };
  },

  setupRoutes: function (router) {
    router.on('route:main', function (qs) {
      this.setState({editing: false});
    }.bind(this));

    router.on('route:edit', function (id, qs) {
      this.setState({editing: true});
    }.bind(this));
  },

  componentWillMount: function () {
    this.setupRoutes(this.props.router);
    Backbone.history.start({pushState: true, root: this.props.appRoot});
  },

  componentWillUpdate: function (nextProps, nextState) {
    this.handleURL(nextState);
  },


  /* State-changing handlers */

  handleEdit: function (e) {
    e.preventDefault();
    this.setState({editing: true});
  },

  handleClose: function () {
    // TODO: check if it should actually switch the state
    // by seeing if the model is dirty (#243)
    this.setState({editing: false});
  },

  handleSave: function (item) {
    this.handleClose();
    window.location.reload();
  },


  /* Handlers */

  handleURL: function (newState) {
    var newURL = newState.editing ? '/edit/' : '/';
    this.props.router.navigate(newURL);
  },


  /* Layout */

  render: function () {
    return (
      <div>
        <div className="edit-profile-btn">
          <button className="btn btn-primary"
                  onClick={this.handleEdit}>
            {gettext('Edit My Public Profile')}
          </button>
        </div>
        <Modal isOpen={this.state.editing}
               handleClose={this.handleClose}>
          <div id="user-edit">
            <h1>{gettext('My Public Profile')}</h1>
            <UserProfileForm model={this.props.user}
                             handleSuccess={this.handleSave} />
          </div>
        </Modal>
      </div>
    );
  }
});


module.exports = UserProfileEdit;
