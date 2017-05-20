/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import 'jquery-magnific-popup';
import 'select2';
import 'jquery-tipsy';
import Spinner from 'spin';

import cookie from 'utils/cookie';
import diff from 'utils/diff';

import agreement from './agreement';
import auth from './auth';
import s2 from './s2';
import browser from './browser';
import captcha from './captcha';
import contact from './contact';
import dropdown from './dropdown';
import helpers from './helpers';
import search from './search';
import stats from './stats';
import configureStore from './store';
import utils from './utils';


Spinner.defaults = {
  lines: 11,
  length: 2,
  width: 5,
  radius: 11,
  rotate: 0,
  corners: 1,
  color: '#000',
  direction: 1,
  speed: 1,
  trail: 50,
  opacity: 1 / 4,
  fps: 20,
  zIndex: 2e9,
  className: 'spinner',
  top: 'auto',
  left: 'auto',
  position: 'relative',
};


// Pootle-specifics. These need to be kept here until:
// 1. they evolve into apps of their own
// 2. they're only used directly as modules from other apps (and they are
//    not referenced like `PTL.<module>.<method>`)

window.PTL = window.PTL || {};

PTL.auth = auth;
PTL.agreement = agreement;
PTL.s2 = s2;
PTL.browser = browser;
PTL.captcha = captcha;
PTL.cookie = cookie;
PTL.contact = contact;
PTL.dropdown = dropdown;
PTL.search = search;
PTL.stats = stats;
PTL.utils = utils;
PTL.utils.diff = diff;


PTL.store = configureStore();


PTL.common = {

  init(opts) {
    PTL.auth.init();
    PTL.s2.init();
    PTL.browser.init(opts);

    if (opts.hasSidebar) {
      helpers.fixSidebarHeight();
      $(window).on('resize', helpers.fixSidebarHeight);
    }

    // Tipsy setup
    $(document).tipsy({
      gravity: $.fn.tipsy.autoBounds2(150, 'n'),
      html: true,
      fade: true,
      delayIn: 750,
      opacity: 1,
      live: '[title], [original-title]',
    });
    setInterval($.fn.tipsy.revalidate, 1000);

    $('form.formtable').on('click', '.js-formtable-select-visible', function () {
      const check = $(this).is(':checked');
      const $formtable = $(this).parents('form.formtable');
      $formtable.find('tbody td.row-select input[type="checkbox"]').each(function () {
        $(this).prop('checked', check);
      });
      if (!check) {
        $formtable.find('input[type="checkbox"].js-formtable-select-all').each(function () {
          $(this).prop('checked', false);
        });
      }
    });

    $('form.formtable').on('click', '.js-formtable-select-all', function () {
      const check = $(this).is(':checked');
      const $formtable = $(this).parents('form.formtable');
      $formtable.find('tbody td.row-select input[type="checkbox"]').each(function () {
        $(this).prop('checked', check);
      });
      $formtable.find('input[type="checkbox"].js-formtable-select-visible').each(function () {
        $(this).prop('checked', check);
      });
    });

    const paginationSelectors = '.js-pagination-page-no input, .js-pagination-items-per-page input';
    $('form.formtable').on('change', paginationSelectors, function () {
      const $formtable = $(this).parents('form.formtable');
      let submit = true;
      $formtable.find(paginationSelectors).each(function () {
        if (!($(this).is(':valid'))) {
          submit = false;
        }
      });
      if (submit) {
        $(this).parents('form.formtable').submit();
      }
    });

    const updateFormtable = ($formtable) => {
      $formtable.find('.js-formtable-messages').each(function () {
        $(this).show();
        $(this).find('ul.messages').each(function () {
          $(this).html(['<li>', gettext('Updating data'), '</li>'].join(''));
        });
      });
    };

    $('form.formtable').on('submit', function () {
      updateFormtable($(this));
    });

    $('form.formtable').on('click', '.js-pagination-next a', function (e) {
      const $formtable = $(this).parents('form.formtable');
      e.preventDefault();
      $formtable.find('.js-pagination-page-no input').each(function () {
        $(this).val(parseInt($(this).val(), 10) + 1);
      });
      $formtable.submit();
    });

    $('form.formtable').on('click', '.js-pagination-previous a', function (e) {
      const $formtable = $(this).parents('form.formtable');
      e.preventDefault();
      $formtable.find('.js-pagination-page-no input').each(function () {
        $(this).val(parseInt($(this).val(), 10) - 1);
        $formtable.submit();
      });
    });

    // Set CSRF token for XHR requests (jQuery-specific)
    $.ajaxSetup({
      traditional: true,
      crossDomain: false,
      beforeSend(xhr, settings) {
        // Set CSRF token only for local requests.
        if (!this.crossDomain &&
            !/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) {
          xhr.setRequestHeader('X-CSRFToken', cookie('csrftoken'));
        }
      },
    });

    /* Collapsing functionality */
    // XXX: crappy code, only used in `term_edit.html`
    $(document).on('click', '.collapse', function collapse(e) {
      e.preventDefault();
      $(this).siblings('.collapsethis').slideToggle('fast');

      if ($('textarea', $(this).next('div.collapsethis')).length) {
        $('textarea', $(this).next('div.collapsethis')).focus();
      }
    });

    /* Page sidebar */
    // TODO: create a named function
    $(document).on('click', '.js-sidebar-toggle', () => {
      const $sidebar = $('.js-sidebar');
      const openClass = 'sidebar-open';
      const cookieName = 'pootle-browser-sidebar';

      $sidebar.toggleClass(openClass);

      const isOpen = $sidebar.hasClass(openClass) ? 1 : 0;

      cookie(cookieName, isOpen, { path: '/' });
    });

    /* Popups */
    $(document).magnificPopup({
      type: 'ajax',
      delegate: '.js-popup-ajax',
      mainClass: 'popup-ajax',
    });

    /* Generic toggle */
    $(document).on('click', '.js-toggle', function toggle(e) {
      e.preventDefault();
      const target = $(this).attr('href') || $(this).data('target');
      $(target).toggle();
    });
  },
};
