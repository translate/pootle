/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';


function updateInputState($checkboxes, $input) {
  if ($checkboxes.length === $checkboxes.filter(':checked').length) {
    $input.prop('disabled', false);
  } else {
    $input.prop('disabled', true);
  }
}


const helpers = {

  fixSidebarHeight() {
    const $body = $('#body');
    const bodyHeight = $body.height();
    const bodyPadding = parseInt($body.css('padding-bottom'), 10);
    const contentAreaHeight = $('#wrapper').height() - $body.offset().top -
                              bodyPadding;

    // Set sidebar width before measuring height of content
    $('#sidebar').css('width', '30%');
    const sidebarHeight = $('#sidebar #sidebar-content').height() +
                          $('#footer').height() + bodyPadding;
    const newHeight = Math.max(contentAreaHeight, sidebarHeight);

    // Remove sidebar width setting - allow CSS to set width
    $('#sidebar').css('width', '');
    if (bodyHeight < newHeight) {
      $body.css('height', newHeight);
    }
  },

  /* Updates the disabled state of an input button according to the
   * checked status of input checkboxes.
   */
  updateInputState(checkboxSelector, inputSelector) {
    const $checkbox = $(checkboxSelector);
    if ($checkbox.length) {
      const $input = $(inputSelector);
      updateInputState($checkbox, $input);
      $checkbox.change(() => {
        updateInputState($checkbox, $input);
      });
    }
  },

};


export default helpers;
