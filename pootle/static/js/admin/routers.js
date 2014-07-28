'use strict';

var Backbone = require('backbone');


var AdminRouter = Backbone.Router.extend({

  routes: {
    '': 'main',
    'edit/:id(/)': 'edit'
  }

});


module.exports = AdminRouter;
