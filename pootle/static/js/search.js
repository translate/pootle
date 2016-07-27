/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import mousetrap from 'mousetrap';
import assign from 'object-assign';

import cookie from 'utils/cookie';


const SEARCH_COOKIE_NAME = 'pootle-search';


const search = {

  init(options) {
    const that = this;

    this.state = {
      searchText: '',
      searchFields: ['source', 'target'],
      searchOptions: [],
    };

    /* Reusable selectors */
    this.$form = $('#search-form');
    this.$container = $('.js-search-container');
    this.$fields = $('.js-search-fields');
    this.$options = $('.js-search-options');
    this.$input = $('#id_search');

    this.settings = assign({
      onSearch: this.onSearch,
    }, options);

    /* Shortcuts */

    mousetrap(document.body).bind('mod+shift+s', (e) => {
      e.preventDefault();
      this.$input.focus();
    });
    mousetrap(this.$form[0]).bind('esc', (e) => {
      e.preventDefault();
      if (this.$form.hasClass('focused')) {
        this.$input.blur();
        this.toggleFields(e);
      }
    });

    this.$input.mouseup((e) => {
      e.preventDefault();
    }).focus(() => {
      this.$input.select();
      this.$form.addClass('focused');
    }).blur(() => {
      if (this.$input.val() === '') {
        this.$input.val(this.state.searchText);
      }
      this.$form.removeClass('focused');
    });

    /* Event handlers */
    this.$input.click((e) => {
      if (search.isOpen()) {
        return;
      }
      this.toggleFields(e);
    });

    this.$input.on('keypress', (e) => {
      if (e.which === 13) {
        this.$form.trigger('submit');
      }
    });
    this.$form.on('submit', this.handleSearch.bind(this));

    /* Necessary to detect clicks out of search.$container */
    $(document).mouseup((e) => {
      if (this.isOpen() &&
          e.target !== that.$input.get(0) &&
          !this.$container.find(e.target).length) {
        this.toggleFields(e);
      }
    });
  },

  setState(newState) {
    this.state = assign({}, this.state, newState);
    this.updateUI();
  },

  /* Dropdown toggling */
  toggleFields(event) {
    event.preventDefault();
    this.$container.toggle();
  },

  /* Returns true if the search drop-down is open */
  isOpen() {
    return this.$container.is(':visible');
  },

  /* Builds search query hash string */
  buildSearchQuery() {
    const { searchText, searchFields, searchOptions } = this.state;
    let query = encodeURIComponent(searchText);

    // If any options have been chosen, append them to the resulting URL
    if (searchFields.length) {
      query += `&sfields=${searchFields.join(',')}`;
    }
    if (searchOptions.length) {
      query += `&soptions=${searchOptions.join(',')}`;
    }

    if (searchFields.length || searchOptions.length) {
      // Remember field selection in a cookie
      const cookieData = {};
      if (searchFields.length) {
        cookieData.sfields = searchFields;
      }
      if (searchOptions.length) {
        cookieData.soptions = searchOptions;
      }

      cookie(SEARCH_COOKIE_NAME, JSON.stringify(cookieData), { path: '/' });
    }

    return query;
  },

  handleSearch(e) {
    e.preventDefault();

    const searchText = this.$input.val();
    const searchOptions = [];
    let searchFields = [];

    this.$fields.find('input:checked').each(function populateFields() {
      searchFields.push($(this).val());
    });
    this.$options.find('input:checked').each(function populateOptions() {
      searchOptions.push($(this).val());
    });

    if (!searchFields.length) {
      searchFields = ['source', 'target'];
    }

    this.setState({
      searchText,
      searchFields,
      searchOptions,
    });

    this.settings.onSearch.call(this, this.state.searchText);
  },

  onSearch(searchText) {
    if (!searchText) {
      return false;
    }

    const hash = `#search=${this.buildSearchQuery()}`;
    window.location = this.$form[0].action + hash;

    return false;
  },

  updateUI() {
    this.$input.val(this.state.searchText).focus();
    const { searchFields, searchOptions } = this.state;

    this.$fields.find('input').each(function updateFieldsProps() {
      $(this).prop('checked', searchFields.indexOf(this.value) !== -1);
    });

    this.$options.find('input').each(function updateOptionsProps() {
      $(this).prop('checked', searchOptions.indexOf(this.value) !== -1);
    });
  },

};


export default search;
