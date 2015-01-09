'use strict';

var Backbone = require('backbone');


var AdminRouter = Backbone.Router.extend({

  routes: {
    '': 'main',
    ':id(/)': 'edit'
  }

});


module.exports = AdminRouter;
