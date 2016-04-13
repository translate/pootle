/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import 'jquery-magnific-popup';
import 'jquery-serializeObject';

import utils from './utils';


function onError(xhr, errorFn) {
  if (xhr.status === 402) {
    display(xhr.responseText);  // eslint-disable-line no-use-before-define
  } else {
    utils.executeFunctionByName(errorFn, window, xhr);
  }
}


function onSubmit(e) {
  e.preventDefault();
  const $form = $(this);
  const reqData = $form.serializeObject();
  const successFn = reqData.sfn;
  const errorFn = reqData.efn;
  const url = $form.attr('action');

  $.ajax({
    url,
    type: 'POST',
    data: reqData,
    success() {
      utils.executeFunctionByName(successFn, window, e);
      $.magnificPopup.close();
    },
    error(xhr) {
      onError(xhr, errorFn);
    },
  });
}


function display(html) {
  $(document).on('submit', '#js-captcha', onSubmit);

  $.magnificPopup.open({
    items: {
      src: html,
      type: 'inline',
    },
    focus: '#id_captcha_answer',
  });
}


export default {
  onError,
};
