(function ($) {

  window.PTL = window.PTL || {};

  PTL.search = {

    init: function (options) {
      /* Reusable selectors */
      this.$form = $("#search-form");
      this.$container = $(".js-search-container");
      this.$fields = $(".js-search-fields");
      this.$options = $(".js-search-options");
      this.$input = $("#id_search");

      /* Default settings */
      this.defaultEnv = "editor";
      this.settings = {
        environment: this.defaultEnv,
        onSubmit: this.onSubmit
      };
      /* Merge given options with default settings */
      if (options) {
        $.extend(this.settings, options);
      }

      /* Shortcuts */
      shortcut.add('ctrl+shift+s', function () {
        PTL.search.$input.focus();
      });
      shortcut.add('escape', function (e) {
        if (PTL.search.$form.hasClass('focused')) {
          PTL.search.$input.blur();
          toggleFields(e);
        }
      });

      /* Search input text */
      $('.js-input-hint').each(function () {
        var initial,
            search = false,
            $label = $(this),
            input = $('#' + $label.attr('for'));

        if (input.prop("defaultValue")) {
          initial = input.prop("defaultValue");
          search = true;
        } else {
          initial = $label.hide().text().replace(':', '');
        }

        input.mouseup(function (e) {
          e.preventDefault();
        }).focus(function () {
          if (input.val() === initial && !search) {
            input.val('');
          }
          input.select();
          PTL.search.$form.addClass('focused');
        }).blur(function () {
          if (input.val() === '') {
            input.val(initial);
          }
          PTL.search.$form.removeClass('focused');
        }).val(initial);
      });

      /* Dropdown toggling */
      var toggleFields = function (event) {
        event.preventDefault();
        PTL.search.$container.toggle();
      };

      /* Event handlers */
      PTL.search.$input.click(function (e) {
        if (PTL.search.isOpen()) {
          return;
        }
        toggleFields(e);
      });

      this.$input.on('keypress', function (e) {
        if (e.which === 13) {
          PTL.search.$form.trigger('submit');
        }
      });
      this.$form.on('submit', this.settings.onSubmit);

      /* Necessary to detect clicks out of PTL.search.$container */
      $(document).mouseup(function (e) {
        if (PTL.search.isOpen() &&
            e.target !== PTL.search.$input.get(0) &&
            !PTL.search.$container.find(e.target).length) {
          toggleFields(e);
        }
      });
    },

    /* Returns true if the search drop-down is open */
    isOpen: function () {
      return this.$container.is(':visible');
    },

    /* Builds search query hash string */
    buildSearchQuery: function (text, remember) {
      var searchFields = [],
          searchOptions = [],
          query = encodeURIComponent(text),
          // Won't remember field choices unless explicitely told so
          remember = remember === undefined ? false : remember;

      // There were no fields specified within the text so we use the dropdown
      PTL.search.$fields.find("input:checked").each(function () {
        searchFields.push($(this).val());
      });
      PTL.search.$options.find("input:checked").each(function () {
        searchOptions.push($(this).val());
      });

      // If any options have been chosen, append them to the resulting URL
      if (remember) {
        if (searchFields.length) {
          query += "&sfields=" + searchFields.join(',');
        }
        if (searchOptions.length) {
          query += "&soptions=" + searchOptions.join(',');
        }
      }

      if (searchFields.length || searchOptions.length) {
        // Remember field selection in a cookie
        var cookieName = "search-" + this.settings.environment,
            cookieData = {};
        if (searchFields.length) {
          cookieData.sfields = searchFields;
        }
        if (searchOptions.length) {
          cookieData.soptions = searchOptions;
        }

        $.cookie(cookieName, JSON.stringify(cookieData), {path: '/'});
      }

      return query;
    },

    onSubmit: function (e) {
      e.preventDefault();

      var s = PTL.search.$input.val();

      if (!s) {
        return false;
      }

      var remember = true,
          hash = "#search=" + PTL.search.buildSearchQuery(s, remember);
      window.location = this.action + hash;

      return false;
    }
  };

}(jQuery));
