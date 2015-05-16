/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

var $ = require('jquery');

require('jquery-magnific-popup');
require('jquery-serializeObject');

var utils = require('./utils.js');


var display = function (html) {
  $(document).on('submit', '#js-captcha', onSubmit);

  $.magnificPopup.open({
    items: {
      src: html,
      type: 'inline'
    },
    focus: '#id_captcha_answer'
  });
};


var onSubmit = function (e) {
  e.preventDefault();
  var $form = $(this),
      reqData = $form.serializeObject(),
      successFn = reqData.sfn,
      errorFn = reqData.efn,
      url = $form.attr('action');

  $.ajax({
    url: url,
    type: 'POST',
    data: reqData,
    success: function () {
      utils.executeFunctionByName(successFn, window, e);
      $.magnificPopup.close();
    },
    error: function (xhr) {
      onError(xhr, errorFn);
    }
  });
};


var onError = function (xhr, errorFn) {
  if (xhr.status === 402) {
    display(xhr.responseText);
  } else {
    utils.executeFunctionByName(errorFn, window, xhr);
  }
};


module.exports = {
  onError: onError,
};
