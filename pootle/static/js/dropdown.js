window.PTL = window.PTL || {};

PTL.dropdown = PTL.dropdown || {};

(function (ns, $) {

  var sel = {
    data: {
      toggle: '[data-action="toggle"]'
    },
    target: '.dropdown-menu',
    targetItems : 'li:not(.menu-divider) a',
    open: 'show-dropdown'
  };

  var keys = {
    ESC: 27,
    UP: 38,
    DOWN: 40
  };


  var DropdownView = Backbone.View.extend({

    events: function () {
      var events = {
        'keydown': 'onKey'
      };
      events['click ' + sel.data.toggle] = 'toggle';

      return events;
    },

    initialize: function () {
      this.$toggle = this.$(sel.data.toggle);
      this.$target = this.$(sel.target);

      $(document).on('click.PTL.dropdown', this.hide.bind(this));
    },

    onKey: function (e) {
      // Avoid hijacking browser keyboard shortcuts when not shown
      if (!this.isVisible()) {
        return true;
      }

      if ([keys.ESC, keys.UP, keys.DOWN].indexOf(e.which) !== -1) {
        e.preventDefault();
      }

      if (e.which === keys.ESC) {
        return this.$toggle.click();
      }

      if ([keys.UP, keys.DOWN].indexOf(e.which) !== -1) {
        var $items = this.$target.find(sel.targetItems);

        if (!$items.length) {
          return false;
        }

        var index = $items.index($items.filter(':focus'));

        if (e.which === keys.UP && index > 0) {
          index--;
        }
        if (e.which === keys.DOWN && index < $items.length - 1) {
          index++;
        }
        if (!index) {
          index = 0;
        }

        $items.eq(index).trigger('focus');
      }
    },

    isVisible: function () {
      return this.$el.hasClass(sel.open);
    },

    show: function () {
      !this.isVisible() && this.$el.addClass(sel.open);
    },

    hide: function () {
      this.isVisible() && this.$el.removeClass(sel.open);
    },

    toggle: function (e) {
      e.preventDefault();
      e.stopPropagation();

      this.$el.toggleClass(sel.open);
      this.$toggle.focus();
    }

  });


  ns.init = function (el) {
    el = el instanceof $ ? el : $(el);
    return new DropdownView({el: el});
  };

}(PTL.dropdown, jQuery));
