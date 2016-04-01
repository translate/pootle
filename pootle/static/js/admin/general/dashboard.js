/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import 'jquery-utils';


/* Sliding table within admin dashboard */
function slideTable(event) {
  event.preventDefault();
  const $node = $('.js-server-extra-stats');

  $.ajax({
    url: l('/admin/more-stats/'),
    dataType: 'json',
    success(data) {
      let newstats = '';
      data.forEach((values) => {
        newstats += `<tr><th scope="row">${values[0]}</th>`
                    + `<td class="stats-number">${values[1]}</td></tr>`;
      });
      $node.append(newstats);
      $node.slideDown('fast');
      $node.next('tbody').remove();
    },
    beforeSend() {
      $(document).off('click', '.slide', slideTable);
      $node.spin();
    },
    complete() {
      $node.spin(false);
    },
    error() {
      $(document).on('click', '.slide', slideTable);
    },
  });
}


const dashboard = {

  init() {
    $(document).on('click', '.slide', slideTable);
  },

};


export default dashboard;
