window.PTL = window.PTL || {};

PTL.models = PTL.models || {};

(function (models, utils) {

/*
 * PTL.models.Unit
 */

models.Unit = Backbone.RelationalModel.extend({

  relations: [{
    type: 'HasOne',
    key: 'store',
    relatedModel: 'PTL.models.Store',
    reverseRelation: {
      key: 'units'
    }
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
  }

});


/*
 * PTL.models.Store
 */

models.Store = Backbone.RelationalModel.extend({});


}(PTL.models, PTL.utils));
