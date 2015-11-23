/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import 'backbone-safesync';
import $ from 'jquery';
import 'jquery-magnific-popup';
import 'jquery-select2';
import 'jquery-tipsy';
import Spinner from 'spin';

import cookie from 'utils/cookie';
import diff from 'utils/diff';

import agreement from './agreement';
import auth from './auth';
import browser from './browser';
import captcha from './captcha';
import contact from './contact';
import dropdown from './dropdown';
import helpers from './helpers';
import score from './score';
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
PTL.browser = browser;
PTL.captcha = captcha;
PTL.cookie = cookie;
PTL.contact = contact;
PTL.dropdown = dropdown;
PTL.score = score;
PTL.search = search;
PTL.stats = stats;
PTL.utils = utils;
PTL.utils.diff = diff;


PTL.store = configureStore();


PTL.common = {

  init(opts) {
    PTL.auth.init();
    PTL.browser.init();

    $(window).load(() => {
      $('body').removeClass('preload');
    });

    if (opts.hasSidebar) {
      helpers.fixSidebarHeight();
      $(window).on('resize', helpers.fixSidebarHeight);
    }

    helpers.updateRelativeDates();
    setInterval(helpers.updateRelativeDates, 6e4);

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

    $('.js-select2').select2({
      width: 'resolve',
    });

    // Set CSRF token for XHR requests (jQuery-specific)
    $.ajaxSetup({
      traditional: true,
      crossDomain: false,
      beforeSend(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) {
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
      const cookieData = JSON.parse(cookie(cookieName)) || {};

      $sidebar.toggleClass(openClass);

      cookieData.isOpen = $sidebar.hasClass(openClass);
      cookie(cookieName, JSON.stringify(cookieData), { path: '/' });
    });

    $(document).on('click', '.js-edit-sidebar-toggle', (e) => {
      e.preventDefault();

      const $sidebar = $('.js-sidebar');
      const $sidebarEditContent = $('.js-sidebar-edit-content');
      const $sidebarContent = $('.js-sidebar-content');
      const openClassName = 'sidebar-edit-open';

      if (!$sidebar.hasClass(openClassName)) {
        const announcementPk = e.target.dataset.announcementPk;

        $.ajax({
          url: `/xhr/announcement/${announcementPk}/edit/`,
          type: 'GET',
          success: (data) => {
            const contentWidth = $sidebarContent.outerWidth();

            $sidebarContent.outerWidth(contentWidth);
            $sidebar.toggleClass(openClassName);

            const sidebarWidth = $sidebar.outerWidth();
            const editContentWidth = contentWidth;

            console.log('Content: ' + contentWidth);
            console.log('Sidebar: ' + sidebarWidth);
            console.log('Edit: ' + editContentWidth);

            $sidebarEditContent.outerWidth(editContentWidth);

            $sidebarEditContent.html(data.formSnippet);

            PTL.commonAdmin.init({
              page: 'staticpages',
              opts: {
                htmlName: data.htmlName,
                initialValue: data.initialValue,
                markup: PTL.settings.MARKUP_FILTER,
              },
            });

            $sidebarEditContent.show();
          },
          complete: (xhr) => {
            if (xhr.status === 400) {
              const formSnippet = $.parseJSON(xhr.responseText).formSnippet;
              $sidebarEditContent.html(data.formSnippet);
              $sidebarEditContent.show();
            }
          },


        });
      }
    });

    $(document).on('click', '.js-cancel-edit-announcement', (e) => {
      e.preventDefault();

      const $sidebar = $('.js-sidebar');
      const $sidebarEditContent = $('.js-sidebar-edit-content');
      const openClassName = 'sidebar-edit-open';

      $sidebarEditContent.hide();
      $sidebarEditContent.html('');
      $sidebar.toggleClass(openClassName);
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

    /* Sorts language names within select elements */
    const ids = ['id_languages', 'id_alt_src_langs', '-language',
                 '-source_language'];

    $.each(ids, (i, id) => {
      const $selects = $(`select[id$="${id}"]`);

      $.each($selects, (j, select) => {
        const $select = $(select);
        const options = $('option', $select);
        let selected;

        if (options.length) {
          if (!$select.is('[multiple]')) {
            selected = $(':selected', $select);
          }

          const opsArray = $.makeArray(options);
          opsArray.sort((a, b) => utils.strCmp($(a).text(), $(b).text()));

          options.remove();
          $select.append($(opsArray));

          if (!$select.is('[multiple]')) {
            $select.get(0).selectedIndex = $(opsArray).index(selected);
          }
        }
      });
    });
  },

};
