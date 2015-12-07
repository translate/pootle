/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import Backbone from 'backbone';
import _ from 'underscore';


const Message = Backbone.Model.extend({
  defaults: {
    text: '',
    level: 'info',
    language: 'en',
  },
});


const MessageList = Backbone.Collection.extend({
  model: Message,
});


const MessageView = Backbone.View.extend({
  className: 'alert alert-block',

  render() {
    this.$el.addClass(['alert', this.model.get('level')].join('-'));
    this.$el.attr('lang', this.model.get('language'));

    this.$el.html(this.model.get('text')).hide().fadeIn(300);

    return this;
  },

});


const MessageListView = Backbone.View.extend({
  el: '.js-alerts',

  initialize() {
    this.subViews = [];

    this.listenTo(this.collection, 'add', this.add);
    this.listenTo(this.collection, 'remove', this.remove);
  },

  add(msg) {
    const msgView = new MessageView({ model: msg });
    this.subViews.push(msgView);

    this.$el.prepend(msgView.render().el);
  },

  remove(msg) {
    const currentView = _.find(this.subViews, (view) => view.model === msg);
    this.subViews = _(this.subViews).without(currentView);

    currentView.$el.fadeOut(3500, () => {
      currentView.remove();
    });
  },

});


const messages = new MessageList();
let messagesView;


const msg = {

  show(opts) {
    if (!messagesView) {
      messagesView = new MessageListView({ collection: messages });
    }
    const message = new Message(opts);

    messages.add(message);

    window.setTimeout(() => {
      messages.remove(message);
    }, 2000);
  },

};


export default msg;
