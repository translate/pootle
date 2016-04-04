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
import 'jquery-utils';

import { updateInputState } from './helpers';


const agreement = {

  init(url) {
    this.url = url;

    $(document).on('click', '.js-agreement-popup', this.displayContent.bind(this));
    $(document).on('submit', '.js-agreement-form', this.onSubmit.bind(this));

    this.display();
  },

  display() {
    $.magnificPopup.open({
      items: {
        src: this.url,
        type: 'ajax',
      },
      callbacks: {
        parseAjax(mfpResponse) {
          // eslint-disable-next-line no-param-reassign
          mfpResponse.data = mfpResponse.data.form;
        },
        ajaxContentAdded() {
          updateInputState('.js-legalfield', '.js-agreement-continue');
        },
      },
      modal: true,
    });
  },

  displayContent(e) {
    e.preventDefault();

    const that = this;
    const url = e.target.href;

    $.magnificPopup.close();
    $.magnificPopup.open({
      items: {
        src: url,
        type: 'ajax',
      },
      callbacks: {
        afterClose: that.display.bind(that),
      },
      mainClass: 'popup-ajax',
    });
  },

  onSubmit(e) {
    e.preventDefault();

    const $agreementBox = $('.js-agreement-box');
    const $agreementForm = $('.js-agreement-form');
    $agreementBox.spin();
    $agreementBox.css({ opacity: 0.5 });

    $.ajax({
      url: $agreementForm.attr('action'),
      type: 'POST',
      data: $agreementForm.serializeObject(),
      success() {
        $.magnificPopup.close();
      },
      complete(xhr) {
        $agreementBox.spin(false);
        $agreementBox.css({ opacity: 1 });

        if (xhr.status === 400) {
          const form = $.parseJSON(xhr.responseText).form;
          $agreementBox.parent().html(form);
        }
      },
    });
  },

};


export default agreement;
