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

var AdminAPIMixin = require('mixins/admin_api');


var Project = Backbone.Model.extend({

  defaults: {
    'code': '',
    'fullname': '',
    'checkstyle': 'standard',
    'localfiletype': 'po',
    'treestyle': 'auto',
    'source_language': '',
    'ignored_files': '',
    'screenshot_search_prefix': '',
    'disabled': false,
  },

  urlRoot: function () {
    return l('/xhr/admin/projects/');
  },

  getAbsoluteUrl: function () {
    return l(['', 'projects', this.get('code'), ''].join('/'));
  },

  getLanguagesUrl: function () {
    return l(['', 'projects', this.get('code'), 'admin', 'languages', ''].join('/'));
  },

  getPermissionsUrl: function () {
    return l(['', 'projects', this.get('code'), 'admin', 'permissions', ''].join('/'));
  },

  getFieldChoices: function (fieldName) {
    if (this.fieldChoices && this.fieldChoices.hasOwnProperty(fieldName)) {
      return this.fieldChoices[fieldName].map(function (field) {
        // FIXME: react-select's issue #25 prevents using non-string values
        return {value: field[0].toString(), label: field[1]};
      });
    }
    return [];
  },

  toJSON: function () {
    var attrs = _.clone(this.attributes);
    attrs.disabled = attrs.disabled ? gettext('disabled') : '';
    return attrs;
  },

});


var ProjectSet = Backbone.Collection.extend(
  _.extend({}, AdminAPIMixin, {

  model: Project,

  url: l('/xhr/admin/projects/'),

}));


module.exports = {
  Project: Project,
  ProjectSet: ProjectSet,
};
