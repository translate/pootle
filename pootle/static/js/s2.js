/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import 'select2';
import _ from 'underscore';


const s2 = {
  init() {
    const searchQuery = { term: '' };

    $('.js-select2').select2({
      minimumResultsForSearch: 10,
      dropdownAutoWidth: true,
      width: 'resolve',
    });
    $('.select2-selection__rendered').removeAttr('title');
    this.templateResult = (result) => [
      '<span class="js-select-resource ', result.css_class, '">',
      this.formatResult(result.text, searchQuery.term),
      '</span>'].join('');
    this.matcher = (query, match) => {
      if (!(query.term)) {
        searchQuery.term = '';
        return match;
      }
      searchQuery.term = query.term;
      if (match.text.toUpperCase().indexOf(query.term.toUpperCase()) !== -1) {
        return match;
      }
      return null;
    };
    this.formatResult = (text, term) => {
      const match = text.toUpperCase().indexOf(term.toUpperCase());
      if (match < 0) {
        return _.escape(text);
      }
      const tl = term.length;
      return [
        _.escape(text.substring(0, match)),
        '<span class="select2-match">',
        _.escape(text.substring(match, match + tl)),
        '</span>',
        _.escape(text.substring(match + tl, text.length)),
      ].join('');
    };
    this.processData = (params) => {
      const result = {
        q: params.term,
        page: params.page,
      };
      return result;
    };
    $(document).ready(() => {
      $('.js-select2-remote').each((i, item) => {
        const $item = $(item);
        $item.select2({
          ajax: {
            url: $(item).data('select2-url'),
            data: (data) => $item.triggerHandler('s2-process-data', data),
            processResults: (results) => $item.triggerHandler('s2-process-results', results),
            method: $(item).data('s2-method') || 'POST',
            dataType: $(item).data('s2-datatype') || 'json',
            delay: $(item).data('s2-delay') || 250,
          },
          cache: true,
          escapeMarkup: (markup) => markup,
          width: $(item).data('s2-width') || 'off',
          dropdownAutoWidth: $(item).data('s2-auto-width') || true,
          allowClear: $(item).data('s2-allow-clear') || false,
          minimumInputLength: $(item).data('s2-min-length') || 3,
          placeholder: $(item).data('s2-placeholder'),
          templateResult: (result) => $item.triggerHandler('s2-template-result', result),
          matcher: (result) => $item.triggerHandler('s2-matcher', result),
        });
      });
    });
  },

};


export default s2;
