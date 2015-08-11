/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

var $ = require('jquery');

var utils = require('./utils.js');


var updateInputState = function ($checkboxes, $input) {
  if ($checkboxes.length === $checkboxes.filter(':checked').length) {
    $input.prop('disabled', false);
  } else {
    $input.prop('disabled', true);
  }
};


var helpers = {

  /* Updates relative dates */
  updateRelativeDates: function () {
    $('.js-relative-date').each(function (i, e) {
      $(e).text(utils.relativeDate(Date.parse($(e).attr('datetime'))));
    });
  },

  fixSidebarHeight: function () {
    var $body = $('#body'),
        bodyHeight = $body.height(),
        bodyPadding = parseInt($body.css('padding-bottom'), 10),
        contentAreaHeight = $('#wrapper').height() - $body.offset().top -
                            bodyPadding,
        sidebarHeight,
        newHeight;

    // Set sidebar width before measuring height of content
    $('#sidebar').css('width', '30%');
    sidebarHeight = $('#sidebar #sidebar-content').height() +
                    $('#footer').height() + bodyPadding;
    newHeight = Math.max(contentAreaHeight, sidebarHeight);

    // Remove sidebar width setting - allow CSS to set width
    $('#sidebar').css('width', '');
    if (bodyHeight < newHeight) {
      $body.css('height', newHeight);
    }
  },

  /* Updates the disabled state of an input button according to the
   * checked status of input checkboxes.
   */
  updateInputState: function (checkboxSelector, inputSelector) {
    var $checkbox = $(checkboxSelector);
    if ($checkbox.length) {
      var $input = $(inputSelector);
      updateInputState($checkbox, $input);
      $checkbox.change(function () {
        updateInputState($checkbox, $input);
      });
    }
  }

};


module.exports = helpers;
