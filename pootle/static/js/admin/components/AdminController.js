/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import Backbone from 'backbone';
import React from 'react';
import _ from 'underscore';

import msg from '../../msg';


const AdminController = React.createClass({

  /* Lifecycle */

  getInitialState() {
    return {
      items: new this.props.adminModule.collection(),
      selectedItem: null,
      searchQuery: '',
      view: 'edit'
    };
  },

  setupRoutes(router) {

    router.on('route:main', (searchQuery) => {
      if (searchQuery === undefined || searchQuery === null) {
        searchQuery = '';
      }
      this.handleSearch(searchQuery);
    });

    router.on('route:edit', (id, qs) => {
      var Model = this.props.adminModule.model;
      var item = new Model({id: id});
      this.handleSelectItem(item);
    });
  },

  componentWillMount() {
    this.setupRoutes(this.props.router);
    Backbone.history.start({pushState: true, root: this.props.appRoot});
  },

  componentWillUpdate(nextProps, nextState) {
    if (nextState.searchQuery !== this.state.searchQuery ||
        nextState.selectedItem !== this.state.selectedItem) {
      this.handleURL(nextState);
    }
  },


  /* State-changing handlers */

  handleSearch(query, extraState) {
    var newState = extraState || {};

    if (query !== this.state.searchQuery) {
      newState.searchQuery = query;
      newState.selectedItem = null;
    }

    return this.state.items.search(query).then(() => {
      newState.items = this.state.items;
      this.setState(newState);
    });
  },

  handleSelectItem(item) {
    var newState = {selectedItem: item, view: 'edit'};

    if (this.state.items.contains(item)) {
      this.setState(newState);
    } else {
      item.fetch().then(() => {
        this.handleSearch(this.state.searchQuery, newState);
      });
    }
  },

  handleAdd() {
    this.setState({selectedItem: null, view: 'add'});
  },

  handleCancel() {
    this.setState({selectedItem: null, view: 'edit'});
  },

  handleSave(item) {
    this.handleSelectItem(item);
    msg.show({
      text: gettext('Saved successfully.'),
      level: 'success'
    });
  },

  handleDelete() {
    this.setState({selectedItem: null});
    msg.show({
      text: gettext('Deleted successfully.'),
      level: 'danger'
    });
  },


  /* Handlers */

  handleURL(newState) {
    let { router } = this.props;
    let query = newState.searchQuery;
    let newURL;

    if (newState.selectedItem) {
      newURL = `/${newState.selectedItem.id}/`;
    } else {
      newURL = query === '' ? '/' : `?q=${encodeURIComponent(query)}`;
    }

    router.navigate(newURL);
  },


  /* Layout */

  render() {
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

      onSearch: this.handleSearch,
      onSelectItem: this.handleSelectItem,
      onAdd: this.handleAdd,
      onCancel: this.handleCancel,
      onSuccess: this.handleSave,
      onDelete: this.handleDelete,
    };

    return (
      <div className="admin-app">
        <this.props.adminModule.Controller {...props} />
      </div>
    );
  }

});


export default AdminController;
