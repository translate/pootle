/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL2
 * license. See the LICENSE file for a copy of the license and the AUTHORS file
 * for copyright and authorship information.
 */

'use strict';

var React = require('react');
var Backbone = require('backbone');
var _ = require('underscore');

var msg = require('../../msg.js');


var AdminApp = React.createClass({

  /* Lifecycle */

  getInitialState: function () {
    return {
      items: new this.props.adminModule.collection(),
      selectedItem: null,
      searchQuery: '',
      view: 'edit'
    };
  },

  setupRoutes: function (router) {

    router.on('route:main', function (qs) {
      var searchQuery = '';
      qs !== undefined && (searchQuery = qs.q);
      this.handleSearch(searchQuery);
    }.bind(this));

    router.on('route:edit', function (id, qs) {
      var Model = this.props.adminModule.model;
      var item = new Model({id: id});
      this.handleSelectItem(item);
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

  handleSearch: function (query, extraState) {
    var newState = extraState || {};

    if (query !== this.state.searchQuery) {
      newState.searchQuery = query;
      newState.selectedItem = null;
    }

    return this.state.items.search(query).then(function () {
      newState.items = this.state.items;
      this.setState(newState);
    }.bind(this));
  },

  handleSelectItem: function (item) {
    var newState = {selectedItem: item, view: 'edit'};

    if (this.state.items.contains(item)) {
      this.setState(newState);
    } else {
      item.fetch().then(function () {
        this.handleSearch(this.state.searchQuery, newState);
      }.bind(this));
    }
  },

  handleAdd: function () {
    this.setState({selectedItem: null, view: 'add'});
  },

  handleCancel: function () {
    this.setState({selectedItem: null, view: 'edit'});
  },

  handleSave: function (item) {
    this.handleSelectItem(item);
    msg.show({
      text: gettext('Saved successfully.'),
      level: 'success'
    });
  },

  handleDelete: function () {
    this.setState({selectedItem: null});
    msg.show({
      text: gettext('Deleted successfully.'),
      level: 'danger'
    });
  },


  /* Handlers */

  handleURL: function (newState) {
    var router = this.props.router,
        query = newState.searchQuery,
        newURL;

    if (newState.selectedItem) {
      newURL = ['', newState.selectedItem.id, ''].join('/');
    } else {
      var params = query === '' ? {} : {q: query};
      newURL = router.toFragment('', params);
    }

    router.navigate(newURL);
  },


  /* Layout */

  render: function () {
    var model = this.props.adminModule.model;

    // Inject dynamic model form choices
    // FIXME: hackish and too far from ideal
    _.defaults(model.prototype, {fieldChoices: {}});
    _.extend(model.prototype.fieldChoices, this.props.formChoices);
    _.extend(model.prototype.defaults, this.props.formChoices.defaults);

    var props = {
      items: this.state.items,
      selectedItem: this.state.selectedItem,
      searchQuery: this.state.searchQuery,
      view: this.state.view,
      collection: this.props.adminModule.collection,
      model: model,

      handleSearch: this.handleSearch,
      handleSelectItem: this.handleSelectItem,
      handleAdd: this.handleAdd,
      handleCancel: this.handleCancel,
      handleSave: this.handleSave,
      handleDelete: this.handleDelete,
    };

    return (
      <div className="admin-app">
        <this.props.adminModule.App {...props} />
      </div>
    );
  }

});


module.exports = AdminApp;
