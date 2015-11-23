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


var Language = Backbone.Model.extend({

  defaults: {
    'code': '',
    'fullname': '',
    'specialchars': '',
    'nplurals': '0',
    'pluralequation': '',
  },

  fieldChoices: {
    'nplurals': [
      // FIXME: using `gettext()` here breaks everything
      [0, 'Unknown'], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 6],
    ],
  },

  urlRoot: function () {
    return l('/xhr/admin/languages/');
  },

  getAbsoluteUrl: function () {
    return l(['', this.get('code'), ''].join('/'));
  },

  getPermissionsUrl: function () {
    return l(['', this.get('code'), 'admin', 'permissions', ''].join('/'));
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

});


var LanguageSet = Backbone.Collection.extend(
  _.extend({}, AdminAPIMixin, {

  model: Language,

  url: l('/xhr/admin/languages/'),

}));


module.exports = {
  Language: Language,
  LanguageSet: LanguageSet,
};
