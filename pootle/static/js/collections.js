window.PTL = window.PTL || {};

PTL.collections = PTL.collections || {};

(function (collections, models) {

/*
 * PTL.collections.Units
 */

collections.UnitCollection = Backbone.Collection.extend({
  model: models.Unit,

  comparator: function (unit) {
    // FIXME: move uIds over the collection
    return PTL.editor.pager.uIds.indexOf(unit.id);
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
