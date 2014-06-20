window.PTL = window.PTL || {};

PTL.user = PTL.user || {};

PTL.models = PTL.models || {};


(function (ns, models, $) {
  'use strict';

  /*
   * PTL.models.User
   */

  models.User = Backbone.Model.extend({
    urlRoot: function () {
      return l('/xhr/users/');
    },

    parse: function (response, options) {
      if (response.hasOwnProperty('form')) {
        this.form = response.form;
        return response.model;
      }

      return response;
    }
  });

  ns.EditFormView = Backbone.View.extend({
    selector: '.js-user-edit-form',

    events: {
      'submit': 'save'
    },

    initialize: function () {
      this.mustReload = false;

      this.model.on('change', function () {
        if (this.model.hasChanged()) {
          this.mustReload = true;
        }
      }, this);
    },

    render: function () {
      this.model.fetch({silent: true}).done(this.openPopup.bind(this));
    },

    openPopup: function () {
      var that = this;
      $.magnificPopup.open({
        items: {
          src: that.model.form,
          type: 'inline'
        },
        mainClass: 'popup-ajax',
        closeOnBgClick: false,
        callbacks: {
          close: function () {
            that.model.trigger('user:edited');
          }
        }
      });
      this.setElement(this.selector);
    },

    save: function (e) {
      e.preventDefault();
      this.model.save(this.$el.serializeObject())
                .done(this.close.bind(this))
                .fail(this.displayErrors.bind(this));
    },

    remove: function () {
      Backbone.View.prototype.remove.apply(this, arguments);
      $.magnificPopup.close();
    },

    close: function () {
      this.remove();

      if (this.mustReload) {
        this.mustReload = false;
        window.location.reload();
      }
    },

    displayErrors: function (xhr) {
      var errors = $.parseJSON(xhr.responseText).errors;
      $('ul.errorlist').remove();

      for (var fieldName in errors) {
        this.validationError(fieldName, errors[fieldName]);
      }
    },

    /* Injects a form validation error next to the input it failed to
     * validate */
    validationError: function (fieldName, msgs) {
      var $field = $('#id_' + fieldName),
          errorList = ['<ul class="errorlist">'];
      for (var i=0; i<msgs.length; i++) {
        errorList.push(['<li>', msgs[i], '</li>'].join(''));
      }
      errorList.push(['</ul>']);

      $field.after(errorList.join(''));
    }
  });

  ns.UserRouter = Backbone.Router.extend({

    initialize: function (userId) {
      this.model = new models.User({id: userId});

      this.editFormView = new ns.EditFormView({model: this.model});

      this.model.on('user:edit', function () {
        this.navigate('/edit/');
      }.bind(this));
      this.model.on('user:edited', function () {
        this.navigate('/');
      }.bind(this));
    },

    routes: {
      '': 'editHome',
      'edit(/)': 'editForm'
    },

    currentView: null,

    switchView: function (view) {
      if (this.currentView) {
        this.currentView.remove();
      }

      if (view !== undefined) {
        view.render();
      }

      this.currentView = view;
    },

    editHome: function () {
      this.switchView();
    },

    editForm: function () {
      this.model.trigger('user:edit');
      this.switchView(this.editFormView);
    }

  });

}(PTL.user, PTL.models, jQuery));
