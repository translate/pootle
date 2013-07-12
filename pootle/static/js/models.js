window.PTL = window.PTL || {};

PTL.models = PTL.models || {};

(function (models) {

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
  }]

});


/*
 * PTL.models.Store
 */

models.Store = Backbone.RelationalModel.extend({});


}(PTL.models));
