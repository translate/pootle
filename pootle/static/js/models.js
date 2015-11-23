/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

var _ = require('underscore');
var Backbone = require('backbone');

require('backbone-relational');

var utils = require('./utils.js');


/*
 * Store
 */

var Store = Backbone.RelationalModel.extend({});


/*
 * Unit
 */

var Unit = Backbone.RelationalModel.extend({

  relations: [{
    type: 'HasOne',
    key: 'store',
    relatedModel: Store,
    reverseRelation: {
      key: 'units',
    },
  }],

  /*
   * Sets the current unit's translation.
   */
  setTranslation: function (value) {
    if (!_.isArray(value)) {
      value = [value];
    }
    this.set('target', _.map(value, function (item) {
      return utils.cleanEscape(item);
    }));
  },

});


module.exports = {
  Store: Store,
  Unit: Unit,
};
