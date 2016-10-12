/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import Backbone from 'backbone';
import _ from 'underscore';

import AdminAPIMixin from 'mixins/admin_api';


const metaUsers = ['nobody', 'default', 'system'];


export const User = Backbone.Model.extend({

  defaults: {
    username: '',
    is_active: true,
    password: '',
    full_name: '',
    email: '',
    is_superuser: false,
    twitter: '',
    linkedin: '',
    website: '',
    bio: '',
  },

  initialize(args, opts) {
    if (opts && opts.urlRoot) {
      this.urlRoot = opts.urlRoot;
    }
  },

  /*
   * URL defaults to the admin backend. Customize when instantiating
   * `User` objects as needed by passing `urlRoot` as opts.
   */
  urlRoot: l('/xhr/admin/users/'),

  getProfileUrl() {
    return l(`/user/${this.get('username')}/`);
  },

  getSettingsUrl() {
    return l(`/user/${this.get('username')}/settings/`);
  },

  isMeta() {
    return metaUsers.indexOf(this.get('username')) !== -1;
  },

});


export const UserSet = Backbone.Collection.extend(
  _.extend({}, AdminAPIMixin, {

    model: User,

    url: l('/xhr/admin/users/'),

  })
);
