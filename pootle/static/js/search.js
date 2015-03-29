/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

var $ = require('jquery');

require('jquery-cookie');

require('shortcut');


var search = {

  init: function (options) {
    var that = this;

    /* Reusable selectors */
    this.$form = $("#search-form");
    this.$container = $(".js-search-container");
    this.$fields = $(".js-search-fields");
    this.$options = $(".js-search-options");
    this.$input = $("#id_search");

    /* Default settings */
    this.settings = {
      environment: 'editor',
      onSubmit: this.onSubmit
    };
    /* Merge given options with default settings */
    if (options) {
      $.extend(this.settings, options);
    }

    /* Shortcuts */
    shortcut.add('ctrl+shift+s', function () {
      this.$input.focus();
    }.bind(this));
    shortcut.add('escape', function (e) {
      if (this.$form.hasClass('focused')) {
        this.$input.blur();
        toggleFields(e);
      }
    }.bind(this));

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

      // XXX: check if so much `that` is necessary
      input.mouseup(function (e) {
        e.preventDefault();
      }).focus(function () {
        if (input.val() === initial && !search) {
          input.val('');
        }
        input.select();
        that.$form.addClass('focused');
      }).blur(function () {
        if (input.val() === '') {
          input.val(initial);
        }
        that.$form.removeClass('focused');
      }).val(initial);
    });

    /* Dropdown toggling */
    var toggleFields = function (event) {
      event.preventDefault();
      that.$container.toggle();
    };

    /* Event handlers */
    this.$input.click(function (e) {
      if (search.isOpen()) {
        return;
      }
      toggleFields(e);
    });

    this.$input.on('keypress', function (e) {
      if (e.which === 13) {
        this.$form.trigger('submit');
      }
    }.bind(this));
    this.$form.on('submit', this.settings.onSubmit.bind(this));

    /* Necessary to detect clicks out of search.$container */
    $(document).mouseup(function (e) {
      if (this.isOpen() &&
          e.target !== that.$input.get(0) &&
          !this.$container.find(e.target).length) {
        toggleFields(e);
      }
    }.bind(this));
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
    this.$fields.find("input:checked").each(function () {
      searchFields.push($(this).val());
    });
    this.$options.find("input:checked").each(function () {
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

    var s = this.$input.val();

    if (!s) {
      return false;
    }

    var remember = true,
        hash = "#search=" + this.buildSearchQuery(s, remember);
    window.location = e.target.action + hash;

    return false;
  }
};


module.exports = search;
