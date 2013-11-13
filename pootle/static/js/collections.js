window.PTL = window.PTL || {};

PTL.collections = PTL.collections || {};

(function (collections, models) {

/*
 * PTL.collections.Units
 */

collections.UnitSet = Backbone.Collection.extend({
  model: models.Unit,

  initialize: function (model, opts) {
    this.chunkSize = opts.chunkSize;
    this.uIds = [];
    this.total = 0;
  },

  comparator: function (unit) {
    return this.uIds.indexOf(unit.id);
  },

  getCurrent: function () {
    return this.activeUnit;
  },
  setCurrent: function (unit) {
    this.activeUnit = unit instanceof this.model ? unit : this.get(unit);
  },
  setFirstAsCurrent: function () {
    this.setCurrent(this.at(0));
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
  }

});


}(PTL.collections, PTL.models));
