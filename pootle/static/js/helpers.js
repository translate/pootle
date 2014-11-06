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
        sidebarHeight = $('#sidebar #staticpage').height() +
                        $('#footer').height() + bodyPadding,
        newHeight = Math.max(contentAreaHeight, sidebarHeight);

    if (bodyHeight < contentAreaHeight) {
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
