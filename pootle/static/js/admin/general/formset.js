/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';


/* Sets background color to table rows when checking delete selects */
function setDeleteBg(e) {
  $(this).parents('tr').toggleClass('delete-selected',
                                    $(e.target).is(':checked'));
}


/* Sets background color to table rows when checking standard selects */
function setSelectedBg(e) {
  if (!$(this).parent().siblings('td[class!=DELETE]')
                       .find('input[type=checkbox][checked]').length) {
    $(this).parents('tr').toggleClass('other-selected',
                                      $(e.target).is(':checked'));
  }
}


/* Selects all checkboxes */
function selectAll(e) {
  const className = e.target.id.split('-').reverse()[0];
  $(`td.${className} input`).prop('checked', $(e.target).is(':checked'));
  $(`td.${className} input`).change();
}


const formset = {

  init() {
    $(document).on('change', 'td.DELETE input[type=checkbox]', setDeleteBg);
    $(document).on('change', 'td[class!=DELETE] input[type=checkbox]',
                   setSelectedBg);

    $(document).on('click', 'th input', selectAll);
  },

};


export default formset;
