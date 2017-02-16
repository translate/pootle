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


const sel = {
  data: {
    target: '[data-action="contact"]',
    subjectPrefix: 'subject-prefix',
    subject: 'subject',
    body: 'body',
  },
  trigger: '.js-contact',
  wrapper: '#js-contact',
  form: '#js-contact form',
  formSent: '#js-sent',
  subject: '#js-contact #id_email_subject',
  body: '#js-contact #id_body',
};


const contact = {

  url: null,

  init(options) {
    if (options) {
      $.extend(this, options);
    }

    $(document).on('click', sel.trigger, (e) => {
      e.preventDefault();
      this.open();
    });
    $(document).on('click', sel.data.target, this.onClick.bind(this));
    $(document).on('submit', sel.form, this.onSubmit.bind(this));
  },

  onClick(e) {
    e.preventDefault();

    const $el = $(e.target);
    const sP = $el.data(sel.data.subjectPrefix);
    const subjectPrefix = sP ? ['[', sP, '] '].join('') : sP;
    const subject = $el.data(sel.data.subject);
    const body = $el.data(sel.data.body);

    this.open({
      subjectPrefix,
      subject,
      body,
    });
  },

  open(opts = {}) {
    const contactUrl = opts.url || this.url;
    if (contactUrl === null) {
      return false;
    }

    $.magnificPopup.open({
      items: {
        src: contactUrl,
        type: 'ajax',
      },
      callbacks: {
        ajaxContentAdded() {
          const newSubject = [];
          if (opts.subjectPrefix) {
            newSubject.push(opts.subjectPrefix);
          }
          if (opts.subject) {
            newSubject.push(opts.subject);
          }
          if (newSubject.length) {
            $(sel.subject).val(newSubject.join(''));
          }
          if (opts.body) {
            $(sel.body).val(opts.body);
          }
        },
      },
      mainClass: 'popup-ajax',
    });
    return true;
  },

  onSubmit(e) {
    e.preventDefault();

    const $form = $(sel.form);
    const url = $form.attr('action');
    const data = $form.serializeObject();
    const captchaCallbacks = {
      sfn: 'PTL.contact.onSubmit',
      efn: 'PTL.contact.onError',
    };
    $.extend(data, captchaCallbacks);

    this.sendMessage(url, data);
  },

  sendMessage(url, data) {
    const that = this;
    $.ajax({
      url,
      data,
      type: 'POST',
      dataType: 'json',
      success: that.onSuccess.bind(that),
      error: that.onError.bind(that),
    });
  },

  onSuccess() {
    // Display thank you message
    $(sel.wrapper).hide();
    $(sel.formSent).show();
  },

  onError(xhr) {
    this.displayErrors(xhr.responseJSON.errors);
  },

  /* Displays errors returned by the contact request */
  displayErrors(errors) {
    $('ul.errorlist').remove();

    for (const fieldName in errors) {
      if (!errors.hasOwnProperty(fieldName)) {
        continue;
      }

      this.validationError(fieldName, errors[fieldName]);
    }
  },

  /* Injects a form validation error next to the input it failed to
   * validate */
  validationError(fieldName, msgs) {
    const $field = $(`#id_${fieldName}`);
    const errorList = ['<ul class="errorlist">'];
    for (let i = 0; i < msgs.length; i++) {
      errorList.push(['<li>', msgs[i], '</li>'].join(''));
    }
    errorList.push(['</ul>']);

    $field.after(errorList.join(''));
  },

};


export default contact;
