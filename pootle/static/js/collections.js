/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

var Backbone = require('backbone');

var Unit = require('./models.js').Unit;


var collections = {};


/*
 * collections.UnitSet
 */

collections.UnitSet = Backbone.Collection.extend({
  model: Unit,

  initialize: function (model, opts) {
    this.chunkSize = opts.chunkSize;
    this.uIds = [];
    this.total = 0;
  },

  comparator: function (unit) {
    return this.uIds.indexOf(unit.id);
  },

  getByUnitId: function (uId) {
    return uId > 0 ? this.get(uId) : this.at(0);
  },

  getCurrent: function () {
    return this.activeUnit;
  },
  setCurrent: function (unit) {
    this.activeUnit = unit instanceof this.model ? unit : this.getByUnitId(unit);
    return this.activeUnit;
  },

  fetchedIds: function () {
    return this.map(function (unit) {
      return unit.id;
    });
  },

  next: function () {
    var index = this.indexOf(this.getCurrent());
    return (index + 1 === this.length) ? null : this.at(index + 1);
  },

  hasNext: function () {
    return this.next() !== null;
  },

  prev: function() {
    var index = this.indexOf(this.getCurrent());
    return (index === 0) ? null : this.at(index - 1);
  },

  hasPrev: function () {
    return this.prev() !== null;
  },

});


module.exports = collections;
