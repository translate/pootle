'use strict';

var Backbone = require('backbone');


var UserProfileRouter = Backbone.Router.extend({

  routes: {
    '': 'main',
    'edit(/)': 'edit'
  }

});


module.exports = UserProfileRouter;
