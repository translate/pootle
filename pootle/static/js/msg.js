/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

var _ = require('underscore');
var Backbone = require('backbone');


var Message = Backbone.Model.extend({
  defaults: {
    text: '',
    level: 'info',
    language: 'en'
  }
});


var MessageList = Backbone.Collection.extend({
  model: Message
});


var MessageView = Backbone.View.extend({
  className: 'alert alert-block',

  render: function () {
    this.$el.addClass(['alert', this.model.get('level')].join('-'));
    this.$el.attr('lang', this.model.get('language'));

    this.$el.html(this.model.get('text')).hide().fadeIn(300);

    return this;
  },

});


var MessageListView = Backbone.View.extend({
  el: '.js-alerts',

  initialize: function () {
    this.subViews = [];

    this.listenTo(this.collection, 'add', this.add);
    this.listenTo(this.collection, 'remove', this.remove);
  },

  add: function (msg) {
    var msgView = new MessageView({model: msg});
    this.subViews.push(msgView);

    this.$el.prepend(msgView.render().el);
  },

  remove: function (msg) {
    var currentView = _.find(this.subViews, function (view) {
      return view.model === msg;
    });
    this.subViews = _(this.subViews).without(currentView);

    currentView.$el.fadeOut(3500, function () {
      currentView.remove();
    });
  }

});


var messages = new MessageList(),
    messagesView;


var msg = {

  show: function (opts) {
    if (!messagesView) {
      messagesView = new MessageListView({collection: messages});
    }
    var msg = new Message(opts);

    messages.add(msg);

    window.setTimeout(function () {
      messages.remove(msg);
    }, 2000);
  }

};


module.exports = msg;
