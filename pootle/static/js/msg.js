window.PTL = window.PTL || {};

PTL.msg = PTL.msg || {};

(function (ns, $) {

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

    template: _.template('<%= text %>'),

    render: function () {
      this.$el.addClass(['alert', this.model.get('level')].join('-'));
      this.$el.attr('lang', this.model.get('language'));

      this.$el.html(this.template(this.model.toJSON())).hide().fadeIn(300);

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

  ns.show = function (opts) {
    if (!messagesView) {
      messagesView = new MessageListView({collection: messages});
    }
    var msg = new Message(opts);

    messages.add(msg);

    window.setTimeout(function () {
      messages.remove(msg);
    }, 2000);
  };

}(PTL.msg, jQuery));
