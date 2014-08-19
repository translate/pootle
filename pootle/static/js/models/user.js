'use strict';

var Backbone = require('backbone');


var metaUsers = ['nobody', 'default', 'system'];


var User = Backbone.Model.extend({

  defaults: {
    'username': '',
    'is_active': true,
    'password': '',
    'full_name': '',
    'email': '',
    'is_superuser': false,
    'twitter': '',
    'linkedin': '',
    'website': '',
    'bio': ''
  },

  // FIXME: change endpoint depending if this is being used by admins
  // or regular users
  urlRoot: function () {
    return l('/xhr/admin/users/');
  },

  getProfileUrl: function () {
    return l(['', 'user', this.get('username'), ''].join('/'));
  },

  displayIndex: function () {
    return this.collection.indexOf(this) + 1;
  },

  parse: function (response, options) {
    if (response.hasOwnProperty('form')) {
      this.form = response.form;
      return response.model;
    }

    return response;
  },

  isMeta: function () {
    return metaUsers.indexOf(this.get('username')) !== -1;
  }
});


var UserSet = Backbone.Collection.extend({
  model: User,

  url: l('/xhr/admin/users/'),

  initialize: function (opts) {
    this.count = 0;
    this.page = 0;
    this.keywords = '';

    this.on('add', this.incrCount);
    this.on('remove', this.decrCount);
  },

  parse: function (response, options) {
    this.count = response.count;

    return response.models;
  },

  comparator: '-id',


  /* Methods */

  incrCount: function () {
    this.count++;
  },

  decrCount: function () {
    this.count--;
  },

  fetchNextPage: function (opts) {
    var newPage = this.page + 1,
        pageData = newPage === 1 ? {} : {p: newPage},
        keywordsData = this.keywords === '' ? {} : {q: this.keywords},
        reqData = _.extend({}, pageData, keywordsData),
        fetchOpts = {remove: false, silent: true, data: reqData};

    _.defaults(fetchOpts, opts);

    return this.fetch(fetchOpts).done(function () {
      this.page = newPage;
    }.bind(this));
  },

  search: function (keywords) {
    var opts = {};
    if (keywords !== this.keywords) {
      this.setSearch(keywords);
      opts = {reset: true};
    }
    return this.fetchNextPage(opts);
  },

  setSearch: function (keywords) {
    this.keywords = keywords;
    this.page = 0;
  }

});


module.exports = {
  User: User,
  UserSet: UserSet
};
