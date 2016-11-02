/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';


window.PTL = window.PTL || {};


PTL.fs = {
  init() {
    const choices = {};
    $.each($('.js-fs-preselect-choices dt'), function () {
      const k = $(this).text();
      const v = $(this).next('dd').text();
      if (v) {
        choices[k] = v;
      }
    });
    $('body').on('select2:select', '.js-select-fs-mapping', (e) => {
      const mapping = choices[$(e.target).val()];
      $('.js-select-fs-mapping-target').val(mapping);
    });
  },
};
