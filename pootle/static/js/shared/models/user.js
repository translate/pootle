/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

var _ = require('underscore');
var Backbone = require('backbone');
var md5 = require('md5').digest_s;

var AdminAPIMixin = require('mixins/admin_api');


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

  initialize: function (args, opts) {
    if (opts && opts.urlRoot) {
      this.urlRoot = opts.urlRoot;
    }
  },

  /*
   * URL defaults to the admin backend. Customize when instantiating
   * `User` objects as needed by passing `urlRoot` as opts.
   */
  urlRoot: l('/xhr/admin/users/'),

  getProfileUrl: function () {
    return l(['', 'user', this.get('username'), ''].join('/'));
  },

  getStatsUrl: function () {
    return l(['', 'user', this.get('username'), 'stats', ''].join('/'));
  },

  getReportsUrl: function () {
    return l(['', 'admin', 'reports',
              '#username=' + this.get('username')].join('/'));
  },

  gravatarUrl: function (size) {
    size = size || '48';
    return [
      'https://secure.gravatar.com/avatar/', md5(this.get('email')),
      '?s=', size, '&d=mm'
    ].join('');
  },

  isMeta: function () {
    return metaUsers.indexOf(this.get('username')) !== -1;
  }
});


var UserSet = Backbone.Collection.extend(
  _.extend({}, AdminAPIMixin, {

  model: User,

  url: l('/xhr/admin/users/'),

}));


module.exports = {
  User: User,
  UserSet: UserSet
};
