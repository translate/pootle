/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import $ from 'jquery';
import 'jquery-cookie';
import assign from 'object-assign';
import 'shortcut';


let search = {

  init: function (options) {
    var that = this;

    this.searchText = '';

    /* Reusable selectors */
    this.$form = $("#search-form");
    this.$container = $(".js-search-container");
    this.$fields = $(".js-search-fields");
    this.$options = $(".js-search-options");
    this.$input = $("#id_search");

    this.settings = assign({
      environment: 'editor',
      onSubmit: this.onSubmit,
    }, options);

    /* Shortcuts */
    shortcut.add('ctrl+shift+s', () => {
      this.$input.focus();
    });
    shortcut.add('escape', (e) => {
      if (this.$form.hasClass('focused')) {
        this.$input.blur();
        toggleFields(e);
      }
    });

    this.$input.mouseup((e) => {
      e.preventDefault();
    }).focus(() => {
      this.$input.select();
      this.$form.addClass('focused');
    }).blur(() => {
      if (this.$input.val() === '') {
        this.$input.val(this.searchText);
      }
      this.$form.removeClass('focused');
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

    this.$input.on('keypress', (e) => {
      if (e.which === 13) {
        this.$form.trigger('submit');
      }
    });
    this.$form.on('submit', this.settings.onSubmit.bind(this));

    /* Necessary to detect clicks out of search.$container */
    $(document).mouseup((e) => {
      if (this.isOpen() &&
          e.target !== that.$input.get(0) &&
          !this.$container.find(e.target).length) {
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
  },

  updateUI(searchText, searchFields, searchOptions) {
    this.searchText = searchText;
    this.$input.val(searchText).focus();

    this.$fields.find('input').each(function () {
      $(this).prop('checked', searchFields.indexOf(this.value) !== -1);
    });

    this.$options.find('input').each(function () {
      $(this).prop('checked', searchOptions.indexOf(this.value) !== -1);
    });
  }

};


export default search;
