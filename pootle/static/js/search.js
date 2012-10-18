(function ($) {

  window.PTL = window.PTL || {};

  PTL.search = {

    init: function (options) {
      /* Reusable selectors */
      this.$fields = $(".js-search-fields");
      this.$fieldsToggle = $(".js-search-fields-toggle");
      this.$iconToggle = this.$fieldsToggle.find("i");
      this.$input = $("#id_search");

      /* Default settings */
      this.defaultEnv = "editor";
      this.settings = {
        environment: this.defaultEnv
      };
      /* Merge given options with default settings */
      if (options) {
        $.extend(this.settings, options);
      }

      /* Regular expressions */
      this.searchRE = /^in:.+|\sin:.+/i;

      /* Valid search field options */
      this.validFieldGroups = {
        editor: ['source', 'target', 'notes', 'locations'],
        terminology: ['source', 'target', 'notes']
      };
      this.validFields = this.validFieldGroups[this.settings['environment']] ||
                         this.validFieldGroups[this.defaultEnv]

      /* Shortcuts */
      shortcut.add('ctrl+shift+s', function () {
        PTL.search.$input.focus().select();
      });
      shortcut.add('escape', function () {
        if (PTL.search.$input.attr("focused")) {
          PTL.search.$input.blur();
        }
      });

      /* Event handlers */
      PTL.search.$input.focus(function() {
        $(this).attr("focused", true);
      });
      PTL.search.$input.blur(function() {
        $(this).attr("focused", "");
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

        input.focus(function () {
          if (input.val() == initial && !search) {
            input.val('');
          }
        }).blur(function () {
          if (input.val() == '') {
            input.val(initial);
          }
        }).val(initial);
      });

      /* Dropdown toggling */
      PTL.search.$fieldsToggle.click(function (event) {
        event.preventDefault();
        PTL.search.$fields.slideToggle();
        PTL.search.$iconToggle.toggleClass("icon-down icon-up");
      });
    },

    /* Parses search text to detect any given fields */
    parse: function (text) {
      var searchFields = [],
          parsed = text;

      // Check if there are fields specified within the search text
      if (this.searchRE.test(text)) {
        var opt,
            removeParts = [],
            parts = text.split(" ");

        $.each(parts, function (i, part) {
          if (PTL.search.searchRE.test(part)) {
            opt = part.split(":")[1];

            // Only consider valid fields
            if ($.inArray(opt, PTL.search.validFields) > -1) {
              searchFields.push(opt);
            }

            // If it's an invalid field name, discard it from the search text
            removeParts.push(i);
          }
        });

        // Remove parsed fields from the original array.
        // It has to be done in reverse order for not clashing with indexes.
        $.each(removeParts.reverse(), function (i, j) {
          parts.splice(j, 1);
        });

        // Join unparsed remaining text, as this will be the actual search text
        parsed = encodeURIComponent(parts.join(" "));
      } else {
        parsed = encodeURIComponent(parsed);
        // There were no fields specified within the text so we use the dropdown
        PTL.search.$fields.find("input:checked").each(function () {
          searchFields.push($(this).val());
        });
      }

      // If any options have been chosen, append them to the resulting URL
      if (searchFields.length) {
        parsed += "&sfields=" + searchFields.join(',');
      }

      if (searchFields.length) {
        // Remember field selection in a cookie
        var cookieName = "search-" + this.settings['environment'],
            cookieData = JSON.stringify(searchFields);
        $.cookie(cookieName, cookieData, {path: '/'});
      }

      return parsed;
    }

  };

})(jQuery);
