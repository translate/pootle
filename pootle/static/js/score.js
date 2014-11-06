'use strict';

var $ = require('jquery');
var Backbone = require('backbone');

require('odometer');


var Score = Backbone.Model.extend({
  validate: function (attrs) {
    var value = attrs.value;

    if (value === undefined || value === null) {
      return 'Not a number';
    }

    if (value % 1 !== 0) {
      return 'Not an integer';
    }
  }
});


var ScoreView = Backbone.View.extend({
  el: '.js-score',

  events: {
    'odometer-digit-added': 'updateWidth',
  },

  updateWidth: function (e) {
    var elWidth = this.$el.find('.odometer-inside').width(),
        newWidth = elWidth === 0 ? 'auto' : elWidth;
    if (this.oldWidth !== newWidth) {
      this.$el.css('width', newWidth);
      this.oldWidth = newWidth;
    }
  },

  initialize: function () {
    this.oldWidth = -1;
    this.updateWidth();
    this.listenTo(this.model, 'change:value', this.render);
  },

  render: function () {
    this.$el.text(this.model.get('value'));
    return this;
  }
});


var scoreModel, scoreView;


var init = function (initialScoreValue) {
  scoreModel = new Score({value: initialScoreValue}, {validate: true});
  scoreView = new ScoreView({model: scoreModel});
};

var set = function (newScore) {
  scoreModel.set({value: newScore}, {validate: true});
  return this;
};

var get = function () {
  return scoreModel.get('value');
};


module.exports = {
  init: init,
  set: set,
  get: get,
};
