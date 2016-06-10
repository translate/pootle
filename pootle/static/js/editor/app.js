/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import _ from 'underscore';
import React from 'react';
import ReactDOM from 'react-dom';

import TimeSince from 'components/TimeSince';
import ReactRenderer from 'utils/ReactRenderer';

// jQuery plugins
import 'jquery-caret';
import 'jquery-easing';
import 'jquery-highlightRegex';
import 'jquery-history';
import 'jquery-serializeObject';
import 'jquery-utils';

// Other plugins
import autosize from 'autosize';
import cx from 'classnames';
import Levenshtein from 'levenshtein';
import mousetrap from 'mousetrap';
import assign from 'object-assign';

import StatsAPI from 'api/StatsAPI';
import UnitAPI from 'api/UnitAPI';
import cookie from 'utils/cookie';
import fetch from 'utils/fetch';
import linkHashtags from 'utils/linkHashtags';

import SuggestionFeedbackForm from './components/SuggestionFeedbackForm';
import UploadTimeSince from './components/UploadTimeSince';

import captcha from '../captcha';
import { UnitSet } from '../collections';
import helpers from '../helpers';
import msg from '../msg';
import score from '../score';
import search from '../search';
import utils from '../utils';
import {
  decodeEntities, escapeUnsafeRegexSymbols, makeRegexForMultipleWords,
} from './utils';


const CTX_STEP = 1;

const ALLOWED_SORTS = ['oldest', 'newest', 'default'];


const filterSelectOpts = {
  dropdownAutoWidth: true,
  width: 'off',
};
const sortSelectOpts = assign({
  minimumResultsForSearch: -1,
}, filterSelectOpts);


const mtProviders = [];


function _refreshChecksSnippet(newChecks) {
  const $checks = $('.js-unit-checks');
  const focusedArea = $('.focusthis')[0];

  $checks.html(newChecks).show();
  utils.blinkClass($checks, 'blink', 4, 200);
  focusedArea.focus();
}


window.PTL = window.PTL || {};


PTL.editor = {

  /* Initializes the editor */
  init(options) {
    /* Default settings */
    this.settings = {
      mt: [],
      displayPriority: false,
    };

    if (options) {
      assign(this.settings, options);
    }

    /* Cached elements */
    this.backToBrowserEl = document.querySelector('.js-back-to-browser');
    this.$editorActivity = $('#js-editor-act');
    this.$editorBody = $('.js-editor-body');
    this.editorTableEl = document.querySelector('.js-editor-table');
    this.$filterStatus = $('#js-filter-status');
    this.$filterChecks = $('#js-filter-checks');
    this.$filterChecksWrapper = $('.js-filter-checks-wrapper');
    this.$filterSortBy = $('#js-filter-sort');
    this.$msgOverlay = $('#js-editor-msg-overlay');
    this.$navNext = $('#js-nav-next');
    this.$navPrev = $('#js-nav-prev');
    this.unitCountEl = document.querySelector('.js-unit-count');
    this.unitIndexEl = document.querySelector('.js-unit-index');
    this.offsetRequested = 0;

    /* Initialize variables */
    this.units = new UnitSet([], {
      chunkSize: this.settings.chunkSize,
    });
    this.editorRow = null;

    this.filter = 'all';
    this.checks = [];
    this.sortBy = 'default';
    this.modifiedSince = null;
    this.user = null;
    this.ctxGap = 0;
    this.ctxQty = parseInt(cookie('ctxQty'), 10) || 1;
    this.preventNavigation = false;

    this.isUnitDirty = false;

    this.isLoading = true;
    this.showActivity();

    this.fetchingOffsets = [];

    /* Regular expressions */
    this.cpRE = /^(<[^>]+>|\[n\|t]|\W$^\n)*(\b|$)/gm;

    /* Levenshtein word comparer */
    this.wordComparer = new Levenshtein({ compare: 'words' });

    /* Compile templates */
    this.tmpl = {
      vUnit: _.template($('#view_unit').html()),
      tm: _.template($('#tm_suggestions').html()),
      editCtx: _.template($('#editCtx').html()),
      msg: _.template($('#js-editor-msg').html()),
    };

    /* Initialize search */
    search.init({
      onSearch: this.onSearch,
    });

    if (options.displayPriority) {
      ALLOWED_SORTS.push('priority');
    }

    /* Select2 */
    this.$filterStatus.select2(filterSelectOpts);
    this.$filterSortBy.select2(sortSelectOpts);

    /* Screenshot images */
    $(document).on('click', '.js-dev-img', function displayScreenshot(e) {
      e.preventDefault();

      $(this).magnificPopup({
        type: 'image',
        gallery: {
          enabled: true,
        },
      }).magnificPopup('open');
    });

    /*
     * Bind event handlers
     */

    /* State changes */
    $(document).on('input', '.js-translation-area',
                   (e) => this.onTextareaChange(e));
    $(document).on('change', 'input.fuzzycheck',
                   () => this.onStateChange());
    $(document).on('click', 'input.fuzzycheck',
                   () => this.onStateClick());
    $(document).on('input', '#id_translator_comment',
                   () => this.handleTranslationChange());

    /* Suggest / submit */
    $(document).on('click', '.switch-suggest-mode a',
                   (e) => this.toggleSuggestMode(e));

    /* Update focus when appropriate */
    $(document).on('focus', '.focusthis', (e) => {
      PTL.editor.focused = e.target;
    });

    /* General */
    $(document).on('click', '.js-editor-reload', (e) => {
      e.preventDefault();
      $.history.load('');
    });

    /* Write TM results, special chars... into the currently focused element */
    $(document).on('click', '.js-editor-copytext', (e) => this.copyText(e));

    /* Copy translator comment */
    $(document).on('click', '.js-editor-copy-comment', (e) => {
      const text = e.currentTarget.dataset.string;
      this.copyComment(text);
    });

    /* Copy original translation */
    $(document).on('click', '.js-copyoriginal', (e) => {
      const uId = e.currentTarget.dataset.uid;
      const sources = [
        ...document.querySelectorAll(`#js-unit-${uId} .js-translation-text`),
      ].map((el) => el.textContent);
      this.copyOriginal(sources);
    });

    /* Editor navigation/submission */
    $(document).on('mouseup', 'tr.view-row, tr.ctx-row', this.gotoUnit);
    $(document).on('keypress', '.js-unit-index', (e) => this.gotoIndex(e));
    $(document).on('dblclick click', '.js-unit-index', (e) => this.unitIndex(e));
    $(document).on('click', 'input.submit', (e) => {
      e.preventDefault();
      this.handleSubmit();
    });
    $(document).on('click', 'input.suggest', (e) => {
      e.preventDefault();
      this.handleSuggest();
    });
    $(document).on('click', '#js-nav-prev', () => this.gotoPrev());
    $(document).on('click', '#js-nav-next', () => this.gotoNext());
    $(document).on('click', '.js-suggestion-reject', (e) => {
      e.stopPropagation();
      this.rejectSuggestion(e.currentTarget.dataset.suggId);
    });
    $(document).on('click', '.js-suggestion-accept', (e) => {
      e.stopPropagation();
      this.acceptSuggestion(e.currentTarget.dataset.suggId);
    });
    $(document).on('click', '.js-suggestion-toggle',
      (e) => this.toggleSuggestion(e, { canHide: true }));

    if (this.settings.canReview) {
      $(document).on('click', '.js-user-suggestion',
        (e) => this.toggleSuggestion(e, { canHide: false }));
    }

    $(document).on('click', '.js-translate-lightbox', () => this.closeSuggestion());

    $(document).on('click', '#js-toggle-timeline', (e) => this.toggleTimeline(e));
    $(document).on('click', '.js-toggle-check', (e) => {
      this.toggleCheck(e.currentTarget.dataset.checkId);
    });

    /* Filtering */
    $(document).on('change', '#js-filter-status', () => this.filterStatus());
    $(document).on('change', '#js-filter-checks', () => this.filterChecks());
    $(document).on('change', '#js-filter-sort', () => this.filterSort());
    $(document).on('click', '.js-more-ctx', () => this.moreContext());
    $(document).on('click', '.js-less-ctx', () => this.lessContext());
    $(document).on('click', '.js-show-ctx', () => this.showContext());
    $(document).on('click', '.js-hide-ctx', () => this.hideContext());

    /* Commenting */
    $(document).on('click', '.js-editor-comment', (e) => {
      e.preventDefault();
      const $elem = $('.js-editor-comment-form');
      const $comment = $('.js-editor-comment');
      $comment.toggleClass('selected');
      if ($comment.hasClass('selected')) {
        $elem.css('display', 'inline-block');
        $('#id_translator_comment').focus();
      } else {
        $elem.css('display', 'none');
      }
    });
    $(document).on('submit', '#js-comment-form', (e) => this.addComment(e));
    $(document).on('click', '.js-comment-remove', (e) => this.removeComment(e));

    /* Misc */
    $(document).on('click', '.js-editor-msg-hide', () => this.hideMsg());

    $(document).on('click', '.js-toggle-raw', (e) => {
      e.preventDefault();
      $('.js-translate-translation').toggleClass('raw');
      $('.js-toggle-raw').toggleClass('selected');
      autosize.update(document.querySelector('.js-translation-area'));
    });

    /* Confirmation prompt */
    window.addEventListener('beforeunload', (e) => {
      if (PTL.editor.isUnitDirty || PTL.editor.isSuggestionFeedbackFormDirty) {
        // eslint-disable-next-line no-param-reassign
        e.returnValue = gettext(
          'You have unsaved changes in this string. Navigating away will discard those changes.'
        );
      }
    });

    /* Bind hotkeys */
    const hotkeys = mousetrap(document.body);

    // FIXME: move binding to `SuggestionFeedbackForm` component
    hotkeys.bind('esc', () => {
      if (this.selectedSuggestionId !== undefined) {
        this.closeSuggestion();
      }
    });
    hotkeys.bind('ctrl+return', () => {
      if (this.isSuggestMode()) {
        this.handleSuggest();
      } else {
        this.handleSubmit();
      }
    });
    hotkeys.bind('ctrl+space', () => this.toggleState());
    hotkeys.bind('ctrl+shift+space', (e) => this.toggleSuggestMode(e));

    hotkeys.bind('ctrl+up', () => this.gotoPrev());
    hotkeys.bind('ctrl+,', () => this.gotoPrev());

    hotkeys.bind('ctrl+down', () => this.gotoNext({ isSubmission: false }));
    hotkeys.bind('ctrl+.', () => this.gotoNext({ isSubmission: false }));

    if (navigator.platform.toUpperCase().indexOf('MAC') >= 0) {
      // Optimize string join with '<br/>' as separator
      this.$navNext.attr('title',
        gettext(
          'Go to the next string (Ctrl+.)<br/><br/>Also:<br/>Next page: ' +
          'Ctrl+Shift+.<br/>Last page: Ctrl+Shift+End'
        )
      );
      this.$navPrev.attr('title',
        gettext(
          'Go to the previous string (Ctrl+,)<br/><br/>Also:</br>Previous page: ' +
          'Ctrl+Shift+,<br/>First page: Ctrl+Shift+Home'
        )
      );
    }

    hotkeys.bind('ctrl+shift+n', (e) => this.unitIndex(e));

    /* XHR activity indicator */
    $(document).ajaxStart(() => {
      clearTimeout(this.delayedActivityTimer);
      this.delayedActivityTimer = setTimeout(() => {
        this.showActivity();
      }, 3000);
    });
    $(document).ajaxStop(() => {
      clearTimeout(this.delayedActivityTimer);
      if (!this.isLoading) {
        this.hideActivity();
      }
    });

    /* Load MT providers */
    this.settings.mt.forEach((provider) => {
      require.ensure([], () => {
        // Retrieve actual module name: FOO_BAR_BAZ => FooBarBaz
        const moduleName = provider.name.split('_').map(
          (x) => x[0] + x.slice(1).toLowerCase()
        ).join('');
        // Webpack doesn't like template strings for now...
        // eslint-disable-next-line prefer-template
        const Module = require('./mt/providers/' + moduleName).default;
        mtProviders.push(new Module(provider.key));
      });
    });

    // Update relative dates every minute
    setInterval(helpers.updateRelativeDates, 6e4);

    /* History support */
    $.history.init((hash) => {
      const params = utils.getParsedHash(hash);
      let isInitial = true;
      let uId = 0;
      let initialOffset = 0;

      if (this.selectedSuggestionId !== undefined) {
        this.closeSuggestion({ checkIfCanNavigate: false });
      }
      ReactRenderer.unmountComponents();

      // Walk through known filtering criterias and apply them to the editor object

      if (params.unit) {
        const uIdParam = parseInt(params.unit, 10);

        if (uIdParam && !isNaN(uIdParam)) {
          const current = this.units.getCurrent();
          const newUnit = this.units.get(uIdParam);

          if (newUnit && newUnit !== current) {
            this.setUnit(newUnit);
            return;
          }

          uId = uIdParam;
          // Don't retrieve initial data if there are existing results
          isInitial = !this.units.length;
        }
      }

      if (params.offset) {
        const offset = parseInt(params.offset, 10);
        if (offset && !isNaN(offset)) {
          initialOffset = this.getStartOfChunk(offset);
        }
      }

      // Reset to defaults
      this.filter = 'all';
      this.checks = [];
      this.category = [];
      this.sortBy = 'default';

      if ('filter' in params) {
        const filterName = params.filter;

        // Set current state
        this.filter = filterName;

        if (filterName === 'checks' && 'checks' in params) {
          this.checks = params.checks.split(',');
        }
        if (filterName === 'checks' && 'category' in params) {
          this.category = params.category;
        }
        if ('sort' in params) {
          const { sort } = params;
          this.sortBy = ALLOWED_SORTS.indexOf(sort) !== -1 ? sort : 'default';
        }
      }

      if ('modified-since' in params) {
        this.modifiedSince = params['modified-since'];
      } else {
        this.modifiedSince = null;
      }

      if ('month' in params) {
        this.month = params.month;
      } else {
        this.month = null;
      }

      // Only accept the user parameter for 'user-*' filters
      if ('user' in params && this.filter.indexOf('user-') === 0) {
        this.user = encodeURIComponent(params.user);
        const user = this.user;

        const values = {
          'user-suggestions':
            // Translators: '%s' is a username
            interpolate(gettext("%s's pending suggestions"), [user]),
          'user-suggestions-accepted':
            // Translators: '%s' is a username
            interpolate(gettext("%s's accepted suggestions"), [user]),
          'user-suggestions-rejected':
            // Translators: '%s' is a username
            interpolate(gettext("%s's rejected suggestions"), [user]),
          'user-submissions':
            // Translators: '%s' is a username
            interpolate(gettext("%s's submissions"), [user]),
          'user-submissions-overwritten':
            // Translators: '%s' is a username, meaning "submissions by %s,
            // that were overwritten"
            interpolate(gettext("%s's overwritten submissions"), [user]),
        };
        const newOpts = [];
        for (const key in values) {
          if (!values.hasOwnProperty(key)) {
            continue;
          }

          newOpts.push(`
            <option value="${key}" data-user="${user}" class="js-user-filter">
              ${values[key]}
            </option>
          `);
        }
        $('.js-user-filter').remove();
        this.$filterStatus.append(newOpts.join(''));
      }

      if ('search' in params) {
        // Note that currently the search, if provided along with the other
        // filters, would override them
        this.filter = 'search';

        const newState = {
          searchText: params.search,
        };

        if ('sfields' in params) {
          newState.searchFields = params.sfields.split(',');
        }
        if ('soptions' in params) {
          newState.searchOptions = params.soptions.split(',');
        }

        search.setState(newState);
      }

      // Update the filter UI to match the current filter

      // disable navigation on UI toolbar events to prevent data reload
      this.preventNavigation = true;

      const filterValue = this.filter === 'search' ? 'all' : this.filter;
      this.$filterStatus.select2('val', filterValue);

      if (this.filter === 'checks') {
        // if the checks selector is empty (i.e. the 'change' event was not fired
        // because the selection did not change), force the update to populate the selector
        if (this.$filterChecks.is(':hidden')) {
          this.getCheckOptions();
        }
      }

      this.$filterSortBy.select2('val', this.sortBy);

      if (this.filter === 'search') {
        this.$filterChecksWrapper.hide();
      }

      // re-enable normal event handling
      this.preventNavigation = false;

      this.fetchUnits({
        uId,
        initialOffset,
        initial: isInitial,
      }).then((hasResults) => {
        if (!hasResults) {
          return;
        }
        if (this.units.uIds.indexOf(uId) === -1) {
          if (this.offsetRequested > this.initialOffset &&
              this.offsetRequested <= this.getOffsetOfLastUnit()) {
            uId = this.units.uIds[this.offsetRequested - this.initialOffset - 1];
          } else {
            uId = this.units.uIds[0];
            $.history.load(utils.updateHashPart('unit', uId));
          }
        }
        this.offsetRequested = 0;
        this.setUnit(uId);
      });
    }, { unescape: true });
  },

  /* Stuff to be done when the editor is ready  */
  ready() {
    const currentUnit = this.units.getCurrent();
    if (currentUnit.get('isObsolete')) {
      this.displayObsoleteMsg();
    }

    autosize(document.querySelector('textarea.expanding:not([disabled="disabled"])'));

    // set direction of the comment body
    $('.extra-item-comment').filter(':not([dir])').bidi();
    // set direction of the suggestion body
    $('.suggestion-translation-body').filter(':not([dir])').bidi();

    // Focus on the first textarea, if any
    const firstArea = $('.focusthis')[0];
    if (firstArea) {
      firstArea.focus();
    }

    const $devComments = $('.js-developer-comments');
    $devComments.html(linkHashtags($devComments.html()));

    if (this.filter === 'search') {
      this.hlSearch();
    }

    if (this.settings.tmUrl !== '') {
      this.getTMUnits();
    }

    if (this.tmData !== null) {
      const tmContent = this.getTMUnitsContent(this.tmData);
      $('#extras-container').append(tmContent);
    }

    this.runHooks();

    this.isUnitDirty = false;
    this.keepState = false;
    this.isLoading = false;
    this.hideActivity();
    this.updateExportLink();
    helpers.updateRelativeDates();
  },

  /* Things to do when no results are returned */
  noResults() {
    this.displayMsg({ body: gettext('No results.') });
    this.reDraw();
  },

  canNavigate() {
    if (this.isUnitDirty || this.isSuggestionFeedbackFormDirty) {
      return window.confirm(  // eslint-disable-line no-alert
        gettext(
          'You have unsaved changes in this string. Navigating away will discard those changes.'
        )
      );
    }

    return true;
  },


  /*
   * Text utils
   */

  /* Highlights search results */
  hlSearch() {
    const { searchText, searchFields, searchOptions } = search.state;
    const selMap = {
      notes: 'div.developer-comments',
      locations: 'div.translate-locations',
      source: 'td.translate-original, .original .js-translation-text',
      target: 'td.translate-translation',
    };

    // Build highlighting selector based on chosen search fields
    const sel = searchFields.map((fieldName) => [
      `tr.edit-row ${selMap[fieldName]}`,
      `tr.view-row ${selMap[fieldName]}`,
    ]).reduce((a, b) => a.concat(b), []);

    let hlRegex;
    if (searchOptions.indexOf('exact') >= 0) {
      hlRegex = new RegExp(`(${escapeUnsafeRegexSymbols(searchText)})`);
    } else {
      hlRegex = new RegExp(makeRegexForMultipleWords(searchText), 'i');
    }
    $(sel.join(', ')).highlightRegex(hlRegex);
  },


  /* Copies text into the focused textarea */
  copyText(e) {
    const $el = $(e.currentTarget);
    const action = $el.data('action');
    const text = $el.data('string') || $el.data('translation-aid') || $el.text();
    const $target = $(this.focused);
    let start;

    if (action === 'overwrite') {
      $target.val(text).trigger('input');
      start = text.length;
    } else {
      start = $target.caret().start + text.length;
      $target.val($target.caret().replace(text)).trigger('input');
    }

    $target.caret(start, start);
    autosize.update(this.focused);
  },


  /* Copies source text(s) into the target textarea(s)*/
  copyOriginal(sources) {
    const targets = $('.js-translation-area');
    if (targets.length) {
      const max = sources.length - 1;

      for (let i = 0; i < targets.length; i++) {
        const newval = sources[i] || sources[max];
        $(targets.get(i)).val(newval).trigger('input');
      }

      // Focus on the first textarea
      const active = $(targets)[0];
      active.focus();
      autosize.update(active);
      // Make this fuzzy
      this.goFuzzy();
      // Place cursor at start of target text
      this.cpRE.exec($(active).val());
      const i = this.cpRE.lastIndex;
      $(active).caret(i, i);
      this.cpRE.lastIndex = 0;
    }
  },

  copyComment(text) {
    const comment = document.querySelector('.js-editor-comment');
    const commentForm = document.querySelector('.js-editor-comment-form');
    const commentInput = document.querySelector('#id_translator_comment');

    if (!comment.classList.contains('selected')) {
      commentForm.style.display = 'inline-block';
      comment.classList.add('selected');
    }

    commentInput.focus();
    commentInput.value = text;
  },


  /*
   * Fuzzying / unfuzzying functions
   */

  /* Sets the current unit's styling as fuzzy */
  doFuzzyStyle() {
    $('tr.edit-row').addClass('fuzzy-unit');
  },


  /* Unsets the current unit's styling as fuzzy */
  undoFuzzyStyle() {
    $('tr.edit-row').removeClass('fuzzy-unit');
  },


  /* Checks the current unit's fuzzy checkbox */
  doFuzzyBox() {
    const $checkbox = $('input.fuzzycheck');
    $checkbox.prop('checked', true);

    if (!this.settings.isAdmin) {
      if (!this.isSuggestMode()) {
        $('.js-fuzzy-block').show();
      }
      $checkbox[0].defaultChecked = true;
    }

    $checkbox.trigger('change');
  },


  /* Unchecks the current unit's fuzzy checkbox */
  undoFuzzyBox() {
    const $checkbox = $('input.fuzzycheck');
    $checkbox.prop('checked', false);
    $checkbox.trigger('change');
  },


  /* Sets the current unit status as fuzzy (both styling and checkbox) */
  goFuzzy() {
    if (!this.isFuzzy()) {
      this.doFuzzyStyle();
      this.doFuzzyBox();
    }
  },


  /* Unsets the current unit status as fuzzy (both styling and checkbox) */
  ungoFuzzy() {
    if (this.isFuzzy()) {
      this.undoFuzzyStyle();
      this.undoFuzzyBox();
    }
  },


  /* Returns whether the current unit is fuzzy or not */
  isFuzzy() {
    return $('input.fuzzycheck').prop('checked');
  },

  toggleFuzzyStyle() {
    if (this.isFuzzy()) {
      this.doFuzzyStyle();
    } else {
      this.undoFuzzyStyle();
    }
  },

  toggleState() {
    // `blur()` prevents a double-click effect if the checkbox was
    // previously clicked using the mouse
    $('input.fuzzycheck:visible').blur().click();
  },

  /* Updates unit textarea and input's `default*` values. */
  updateUnitDefaultProperties() {
    $('.js-translation-area').each(function setDefaultValue() {
      this.defaultValue = this.value;
    });
    const checkbox = document.querySelector('#id_state');
    checkbox.defaultChecked = checkbox.checked;
    this.handleTranslationChange();
  },

  /* Updates comment area's `defaultValue` value. */
  updateCommentDefaultProperties() {
    const comment = document.querySelector('#id_translator_comment');
    comment.defaultValue = comment.value;
    this.handleTranslationChange();
  },

  handleTranslationChange() {
    const comment = document.querySelector('#id_translator_comment');
    const commentChanged = comment !== null ?
                           comment.value !== comment.defaultValue : false;

    const submit = document.querySelector('.js-submit');
    const suggest = document.querySelector('.js-suggest');
    const translations = $('.js-translation-area').get();
    const suggestions = $('.js-user-suggestion').map(function getSuggestions() {
      return $(this).data('translation-aid');
    }).get();
    const checkbox = document.querySelector('#id_state');
    const stateChanged = checkbox.defaultChecked !== checkbox.checked;

    let areaChanged = false;
    let needsReview = false;
    let suggestionExists = false;
    let area;

    // Non-admin users are required to clear the fuzzy checkbox
    if (!this.settings.isAdmin) {
      needsReview = checkbox.checked === true;
    }

    for (let i = 0; i < translations.length && !areaChanged; i++) {
      area = translations[i];
      areaChanged = area.defaultValue !== area.value;
    }

    if (suggestions.length) {
      for (let i = 0; i < translations.length && !suggestionExists; i++) {
        area = translations[i];
        suggestionExists = suggestions.indexOf(area.value) !== -1;
      }
    }

    // Store dirty state for the current unit
    this.isUnitDirty = areaChanged || stateChanged || commentChanged;

    if (submit !== null) {
      submit.disabled = !(stateChanged || areaChanged) || needsReview;
    }
    if (suggest !== null) {
      suggest.disabled = !areaChanged || suggestionExists;
    }
  },

  onStateChange() {
    this.handleTranslationChange();

    this.toggleFuzzyStyle();
  },

  onStateClick() {
    // Prevent automatic unfuzzying on explicit user action
    this.keepState = true;
  },

  onTextareaChange(e) {
    this.handleTranslationChange();

    const el = e.target;
    const hasChanged = el.defaultValue !== el.value;

    if (hasChanged && !this.keepState) {
      this.ungoFuzzy();
    }

    clearTimeout(this.similarityTimer);
    this.similarityTimer = setTimeout(() => {
      this.checkSimilarTranslations();
      this.similarityTimer = null;  // So we know the code was run
    }, 200);
  },


  /*
   * Translation's similarity
   */

  getSimilarityData() {
    const currentUnit = this.units.getCurrent();
    return {
      similarity: currentUnit.get('similarityHuman'),
      mt_similarity: currentUnit.get('similarityMT'),
    };
  },

  calculateSimilarity(newTranslation, $elements, dataSelector) {
    let maxSimilarity = 0;
    let boxId = null;

    for (let i = 0; i < $elements.length; i++) {
      const $element = $elements.eq(i);
      const aidText = $element.data(dataSelector);
      const similarity = this.wordComparer.similarity(newTranslation, aidText);

      if (similarity > maxSimilarity) {
        maxSimilarity = similarity;
        boxId = $element.hasClass('js-translation-area') ?
                null : $element.val('id');
      }
    }

    return {
      boxId,
      max: maxSimilarity,
    };
  },

  checkSimilarTranslations() {
    const dataSelector = 'translation-aid';
    const dataSelectorMT = 'translation-aid-mt';
    const $aidElementsMT = $(`[data-${dataSelectorMT}]`);

    let aidElementsSelector = `[data-${dataSelector}]`;

    // Exclude own suggestions for non-anonymous users
    if (!this.settings.isAnonymous) {
      aidElementsSelector += `[data-suggestor-id!=${this.settings.userId}]`;
    }

    const $aidElements = $(aidElementsSelector);

    if (!$aidElements.length && !$aidElementsMT.length) {
      return false;
    }

    const currentUnit = this.units.getCurrent();
    const newTranslation = $('.js-translation-area').val();
    let simHuman = { max: 0, boxId: null };
    let simMT = { max: 0, boxId: null };

    if ($aidElements.length) {
      simHuman = this.calculateSimilarity(newTranslation, $aidElements,
                                          dataSelector);
    }
    if ($aidElementsMT.length) {
      simMT = this.calculateSimilarity(newTranslation, $aidElementsMT,
                                       dataSelectorMT);
    }

    currentUnit.set({
      similarityHuman: simHuman.max,
      similarityMT: simMT.max,
    });

    const similarity = (simHuman.max > simMT.max) ? simHuman : simMT;
    this.highlightBox(similarity.boxId, similarity.max === 1);
    return true;
  },

  /* Applies highlight classes to `boxId`. */
  highlightBox(boxId, isExact) {
    const bestMatchCls = 'best-match';
    const exactMatchCls = 'exact-match';

    $('.translate-table').find(`.${bestMatchCls}`)
                         .removeClass(`${bestMatchCls} ${exactMatchCls}`);

    if (boxId === null) {
      return false;
    }

    $(boxId).addClass(cx({
      [bestMatchCls]: true,
      [exactMatchCls]: isExact,
    }));
    return true;
  },


  /*
   * Suggest / submit mode functions
   */

  /* Changes the editor into suggest mode */
  doSuggestMode() {
    this.editorTableEl.classList.add('suggest-mode');
  },


  /* Changes the editor into submit mode */
  undoSuggestMode() {
    this.editorTableEl.classList.remove('suggest-mode');
  },


  /* Returns true if the editor is in suggest mode */
  isSuggestMode() {
    return this.editorTableEl.classList.contains('suggest-mode');
  },


  /* Toggles suggest/submit modes */
  toggleSuggestMode(e) {
    e.preventDefault();
    if (this.isSuggestMode()) {
      this.undoSuggestMode();
    } else {
      this.doSuggestMode();
    }
  },

  updateExportLink() {
    const $exportOpt = $('.js-export-view');
    const baseUrl = $exportOpt.data('export-url');
    const hash = utils.getHash().replace(/&?unit=\d+/, '');
    const exportLink = hash ? `${baseUrl}?${hash}` : baseUrl;

    $exportOpt.data('href', exportLink);
  },

  /*
   * Indicators, messages, error handling
   */

  showActivity() {
    this.hideMsg();
    this.$editorActivity.spin().fadeIn(300);
  },

  hideActivity() {
    this.$editorActivity.spin(false).fadeOut(300);
  },

  /* Displays an informative message */
  displayMsg({ showClose = true, body = null }) {
    this.hideActivity();
    helpers.fixSidebarHeight();
    this.$msgOverlay.html(
      this.tmpl.msg({ showClose, body })
    ).fadeIn(300);
  },

  hideMsg() {
    if (this.$msgOverlay.length) {
      this.$msgOverlay.fadeOut(300);
    }
  },

  /* Displays error messages on top of the toolbar */
  displayError(text) {
    this.hideActivity();
    msg.show({ text, level: 'error' });
  },


  /* Handles XHR errors */
  error(xhr, s) {
    let text = '';

    if (s === 'abort') {
      return;
    }

    if (xhr.status === 0) {
      text = gettext('Error while connecting to the server');
    } else if (xhr.status === 402) {
      captcha.onError(xhr, 'PTL.editor.error');
    } else if (xhr.status === 404) {
      text = gettext('Not found');
    } else if (xhr.status === 500) {
      text = gettext('Server error');
    } else if (s === 'timeout') {
      text = gettext('The server seems down. Try again later.');
    } else {
      text = $.parseJSON(xhr.responseText).msg;
    }

    PTL.editor.displayError(text);
  },

  displayObsoleteMsg() {
    const msgText = gettext('This string no longer exists.');
    const backMsg = gettext('Go back to browsing');
    const backLink = this.backToBrowserEl.getAttribute('href');
    const reloadMsg = gettext('Reload page');
    const html = [
      '<div>', msgText, '</div>',
      '<div class="editor-msg-btns">',
      '<a class="btn btn-xs js-editor-reload" href="#">', reloadMsg, '</a>',
      '<a class="btn btn-xs" href="', backLink, '">', backMsg, '</a>',

      '</div>',
    ].join('');

    this.displayMsg({ body: html, showClose: false });
  },


  /*
   * Misc functions
   */

  /* Gets the offset of a unit in the total result set */
  getOffsetOfUid(uid) {
    return this.initialOffset + this.units.uIds.indexOf(uid);
  },

  /* Gets the start offset for the chunk of a given offset */
  getStartOfChunk(offset) {
    return offset - (offset % (2 * this.units.chunkSize));
  },

  /* Checks whether editor needs the next batch of units */
  needsNextUnitBatch() {
    return (
      this.units.uIds.slice(-7).indexOf(this.units.activeUnit.id) !== -1 &&
      this.getOffsetOfLastUnit() < this.units.total
    );
  },

  /* Checks whether editor needs the previous batch of units */
  needsPreviousUnitBatch() {
    return (
      this.units.uIds.slice(0, 7).indexOf(this.units.activeUnit.id) !== -1 &&
      this.initialOffset > 0
    );
  },

  /* Returns the uids of the last batch of units currently stored */
  getPreviousUids() {
    return this.units.uIds.slice(-(2 * this.units.chunkSize));
  },

  /* Sets the offset in the browser location */
  setOffset(uid) {
    $.history.load(utils.updateHashPart(
      'offset', this.getStartOfChunk(this.getOffsetOfUid(uid)))
    );
  },

  /* Gets the offset of the last unit currently held by the client */
  getOffsetOfLastUnit() {
    return this.initialOffset + this.units.uIds.length;
  },

  /* Remembers offsets that are currently being fetched to prevent multiple
   * calls to same URL
   */
  markAsFetching(offset) {
    this.fetchingOffsets.push(offset);
  },

  /* Removes remembered offsets once the XHR call has completed */
  markAsFetched(offset) {
    if (this.fetchingOffsets.indexOf(offset) !== -1) {
      this.fetchingOffsets = this.fetchingOffsets.splice(
        this.fetchingOffsets.indexOf(offset), 1
      );
    }
  },

  /* Returns true if client is awaiting a get_units call with given offset */
  isBeingFetched(offset) {
    return this.fetchingOffsets.indexOf(offset) !== -1;
  },

  /* Gets common request data */
  getReqData() {
    const reqData = {};

    if (this.filter === 'checks' && this.checks.length) {
      reqData.checks = this.checks.join(',');
    }
    if (this.filter === 'checks' && this.category.length) {
      reqData.category = this.category;
    }


    if (this.filter === 'search') {
      const { searchText, searchFields, searchOptions } = search.state;
      reqData.search = searchText;
      reqData.sfields = searchFields;
      reqData.soptions = searchOptions;
    } else {
      reqData.filter = this.filter;
      if (this.sortBy !== 'default') {
        reqData.sort = this.sortBy;
      }
    }

    if (this.modifiedSince !== null) {
      reqData['modified-since'] = this.modifiedSince;
    }

    if (this.user) {
      reqData.user = this.user;
    }

    return reqData;
  },


  /*
   * Unit navigation, display, submission
   */


  /* Renders a single row */
  renderRow(unit) {
    return (`
      <tr id="row${unit.id}" class="view-row">
        ${this.tmpl.vUnit({ unit: unit.toJSON() })}
      </tr>
    `);
  },

  renderEditorRow(unit) {
    const eClass = cx('edit-row', {
      'fuzzy-unit': unit.get('isfuzzy'),
      'with-ctx': this.filter !== 'all',
    });

    const [ctxRowBefore, ctxRowAfter] = this.renderCtxControls({ hasData: false });

    return (`
      ${this.filter !== 'all' ? ctxRowBefore : ''}
      <tr id="row${unit.id}" class="${eClass}">
        ${this.editorRow}
      </tr>
      ${this.filter !== 'all' ? ctxRowAfter : ''}
    `);
  },

  /* Renders the editor rows */
  renderRows() {
    const unitGroups = this.getUnitGroups();
    const currentUnit = this.units.getCurrent();

    const rows = [];

    unitGroups.forEach((unitGroup) => {
      // Don't display a delimiter row if all units have the same origin
      if (unitGroups.length !== 1) {
        rows.push(
          '<tr class="delimiter-row"><td colspan="2">' +
            `<div class="hd"><h2>${_.escape(unitGroup.path)}</h2></div>` +
          '</td></tr>'
        );
      }

      for (let i = 0; i < unitGroup.units.length; i++) {
        const unit = unitGroup.units[i];

        if (unit.id === currentUnit.id) {
          rows.push(this.renderEditorRow(unit));
        } else {
          rows.push(this.renderRow(unit));
        }
      }
    });

    return rows.join('');
  },


  /* Renders context rows for units passed as 'units' */
  renderCtxRows(units, extraCls) {
    const currentUnit = this.units.getCurrent();
    let rows = '';

    for (let i = 0; i < units.length; i++) {
      // FIXME: Please let's use proper models for context units
      let unit = units[i];
      unit = assign({}, currentUnit.toJSON(), unit);

      rows += `<tr id="ctx${unit.id}" class="ctx-row ${extraCls}">`;
      rows += this.tmpl.vUnit({ unit });
      rows += '</tr>';
    }

    return rows;
  },


  /* Returns the unit groups for the current editor state */
  getUnitGroups() {
    const limit = parseInt(((this.units.chunkSize - 1) / 2), 10);
    const unitCount = this.units.length;
    const currentUnit = this.units.getCurrent();
    const curIndex = this.units.indexOf(currentUnit);

    let begin = curIndex - limit;
    let end = curIndex + 1 + limit;
    let prevPath = null;

    if (begin < 0) {
      end = end + -begin;
      begin = 0;
    } else if (end > unitCount) {
      if (begin > end - unitCount) {
        begin = begin + -(end - unitCount);
      } else {
        begin = 0;
      }
      end = unitCount;
    }

    return this.units.slice(begin, end).reduce((out, unit) => {
      const pootlePath = unit.get('store').get('pootlePath');

      if (pootlePath === prevPath) {
        out[out.length - 1].units.push(unit);
      } else {
        out.push({
          path: pootlePath,
          units: [unit],
        });
      }

      prevPath = pootlePath;

      return out;
    }, []);
  },


  /* Sets the edit view for the current active unit */
  renderUnit() {
    if (this.units.length) {
      this.hideMsg();

      this.reDraw(this.renderRows());
    }
  },


  /* reDraws the translate table rows */
  reDraw(newTbody) {
    const $oldRows = this.$editorBody.find('tr');

    // Remove autosize event listeners for textarea before removing
    autosize.destroy(document.querySelectorAll('textarea.expanding'));

    $oldRows.remove();

    if (newTbody !== undefined) {
      this.$editorBody.append(newTbody);

      this.ready();
    }
  },


  /* Updates a button in `selector` to the `disable` state */
  updateNavButton($button, disable) {
    // Avoid unnecessary actions
    if ($button.is(':disabled') && disable || $button.is(':enabled') && !disable) {
      return;
    }

    if (disable) {
      $button.data('title', $button.attr('title'));
      $button.removeAttr('title');
    } else {
      $button.attr('title', $button.data('title'));
    }
    $button.prop('disabled', disable);
  },


  /* Updates the navigation widget */
  updateNavigation() {
    this.updateNavButton(this.$navPrev,
                         this.initialOffset === 0 && !this.units.hasPrev());
    this.updateNavButton(this.$navNext, !this.units.hasNext());

    this.unitCountEl.textContent = this.units.frozenTotal;

    const currentUnit = this.units.getCurrent();
    if (currentUnit !== undefined) {
      if (this.offsetRequested === 0) {
        this.unitIndexEl.textContent = (
          this.units.uIds.indexOf(currentUnit.id) + 1 + this.initialOffset
        );
      }
    }
  },

  /* Fetches more units in case they are needed */
  fetchUnits({ initial = false, uId = 0, initialOffset = 0 } = {}) {
    let offsetToFetch = -1;
    let uidToFetch = -1;
    let previousUids = [];
    if (initial) {
      this.initialOffset = -1;
      this.offset = 0;
      if (uId > 0) {
        uidToFetch = uId;
      }
      if (initialOffset > 0) {
        offsetToFetch = initialOffset;
        this.initialOffset = initialOffset;
      }
    } else if (this.units.length && this.units.total) {
      if (this.needsNextUnitBatch()) {
        // The unit is in the last 7, try and get the next chunk - also sends
        // the last chunk of uids to allow server to adjust results
        previousUids = this.getPreviousUids();
        offsetToFetch = this.offset;
      } else if (this.needsPreviousUnitBatch()) {
        // The unit is in the first 7, try and get the previous chunk
        offsetToFetch = Math.max(this.initialOffset - (2 * this.units.chunkSize), 0);
      }
    }
    if (initial || uidToFetch > -1 ||
        (offsetToFetch > -1 && !this.isBeingFetched(offsetToFetch))) {
      const reqData = {
        path: this.settings.pootlePath,
      };
      assign(reqData, this.getReqData());
      if (offsetToFetch > -1) {
        this.markAsFetching(offsetToFetch);
        if (offsetToFetch > 0) {
          reqData.offset = offsetToFetch;
        }
      }
      if (uidToFetch > -1) {
        reqData.uids = uidToFetch;
      }
      if (previousUids.length > 0) {
        reqData.previous_uids = previousUids;
      }
      return UnitAPI.fetchUnits(reqData)
        .then(
          (data) => this.storeUnitData(data),
          this.error
        ).always(() => this.markAsFetched(offsetToFetch));
    }
    /* eslint-disable new-cap */
    return $.Deferred((deferred) => deferred.reject(false));
    /* eslint-enable new-cap */
  },

  storeUnitData(data) {
    const { total } = data;
    const { start } = data;
    const { end } = data;
    let { unitGroups } = data;
    let prependUnits = false;

    if (!unitGroups.length && !this.units.uIds.length) {
      this.noResults();
      return false;
    }
    if (this.offset === 0) {
      this.units.reset();
      this.units.uIds = [];
      this.units.frozenTotal = total;
    }
    if (this.initialOffset === -1) {
      this.initialOffset = start;
      this.units.frozenTotal = total;
    } else if (start < this.initialOffset) {
      this.initialOffset = start;
      prependUnits = true;
      unitGroups = unitGroups.reverse();
    }
    for (let i = 0; i < unitGroups.length; i++) {
      const unitGroup = unitGroups[i];
      for (const pootlePath in unitGroup) {
        if (!unitGroup.hasOwnProperty(pootlePath)) {
          continue;
        }
        const group = unitGroup[pootlePath];
        const store = assign({ pootlePath }, group.meta);
        const units = group.units.map(
          (unit) => assign(unit, { store })  // eslint-disable-line no-loop-func
        );
        if (prependUnits) {
          this.units.set(units, { remove: false, at: 0 });
          // eslint-disable-next-line no-loop-func
          units.reverse().map((unit) => this.units.uIds.unshift(unit.id));
        } else {
          this.units.set(units, { remove: false, at: this.units.length });
          // eslint-disable-next-line no-loop-func
          units.map((unit) => this.units.uIds.push(unit.id));
        }
      }
    }
    this.offset = end;
    this.units.total = total;
    this.updateNavigation();
    return true;
  },

  /* Stores editor data for the current unit */
  setEditUnit(data) {
    const currentUnit = this.units.getCurrent();
    currentUnit.set('isObsolete', data.is_obsolete);
    currentUnit.set('sources', data.sources);

    this.tmData = data.tm_suggestions || null;
    this.editorRow = data.editor;
  },

  /* Sets a new unit as the current one, rendering it as well */
  setUnit(unit) {
    const newUnit = this.units.setCurrent(unit);
    const body = {};
    if (this.settings.vFolder) {
      body.vfolder = this.settings.vFolder;
    }
    this.fetchUnits().always(() => {
      this.updateNavigation();
      UnitAPI.fetchUnit(newUnit.id, body)
        .then(
          (data) => {
            this.setEditUnit(data);
            this.renderUnit();
          },
          this.error
        );
    });
  },

  /* Pushes translation submissions and moves to the next unit */
  handleSubmit(comment = '') {
    const el = document.querySelector('input.submit');
    const newTranslation = $('.js-translation-area')[0].value;
    const suggestions = $('.js-user-suggestion').map(function getSuggestions() {
      return {
        text: this.dataset.translationAid,
        id: this.dataset.suggId,
      };
    }).get();
    const captchaCallbacks = {
      sfn: 'PTL.editor.processSubmission',
      efn: 'PTL.editor.error',
    };

    const body = $('#translate').serializeObject();

    this.updateUnitDefaultProperties();

    // Check if the string being submitted is already in the set of
    // suggestions
    // FIXME: this is LAME, I wanna die: we need to use proper models!!
    const suggestionIds = _.pluck(suggestions, 'id');
    const suggestionTexts = _.pluck(suggestions, 'text');
    const suggestionIndex = suggestionTexts.indexOf(newTranslation);

    if (suggestionIndex !== -1 && !this.isFuzzy()) {
      this.acceptSuggestion(suggestionIds[suggestionIndex], { skipToNext: true });
      return;
    }

    // If similarities were in the process of being calculated by the time
    // the submit button was clicked, clear the timer and calculate them
    // straight away
    if (this.similarityTimer !== null) {
      clearTimeout(this.similarityTimer);
      this.checkSimilarTranslations();
    }

    assign(body, this.getReqData(), this.getSimilarityData(), captchaCallbacks);

    el.disabled = true;

    // Check if we used a suggestion
    if (this.selectedSuggestionId !== undefined) {
      const suggData = {
        suggestion: this.selectedSuggestionId,
        comment,
      };
      assign(body, suggData);
    }

    UnitAPI.addTranslation(this.units.getCurrent().id, body)
      .then(
        (data) => this.processSubmission(data),
        this.error
      );
  },

  processSubmission(data) {
    if (this.selectedSuggestionId !== undefined) {
      this.processAcceptSuggestion(data, this.selectedSuggestionId);
      return;
    }

    // FIXME: handle this via events
    const translations = $('.js-translation-area').map((i, el) => $(el).val())
                                                  .get();

    const unit = this.units.getCurrent();
    unit.setTranslation(translations);
    unit.set('isfuzzy', this.isFuzzy());

    const hasCriticalChecks = !!data.checks;
    $('.translate-container').toggleClass('error', hasCriticalChecks);

    if (data.user_score) {
      score.set(data.user_score);
    }

    if (hasCriticalChecks) {
      _refreshChecksSnippet(data.checks);
    } else {
      this.gotoNext();
    }
  },

  /* Pushes translation suggestions and moves to the next unit */
  handleSuggest() {
    const captchaCallbacks = {
      sfn: 'PTL.editor.processSuggestion',
      efn: 'PTL.editor.error',
    };

    const body = $('#translate').serializeObject();

    this.updateUnitDefaultProperties();

    // in suggest mode, do not send the fuzzy state flag
    // even if it is set in the form internally
    delete body.state;

    assign(body, this.getReqData(), this.getSimilarityData(), captchaCallbacks);

    UnitAPI.addSuggestion(this.units.getCurrent().id, body)
      .then(
        (data) => this.processSuggestion(data),
        this.error
      );
  },

  processSuggestion(data) {
    if (data.user_score) {
      score.set(data.user_score);
    }

    this.gotoNext();
  },


  /* Loads the previous unit */
  gotoPrev() {
    if (!this.canNavigate()) {
      return false;
    }

    const newUnit = this.units.prev();
    if (newUnit) {
      const newHash = utils.updateHashPart('unit', newUnit.id);
      $.history.load(newHash);
      this.setOffset(newUnit.id);
    }
    return true;
  },


  /* Loads the next unit */
  gotoNext(opts = { isSubmission: true }) {
    if (!this.canNavigate()) {
      return false;
    }
    const newUnit = this.units.next();
    if (newUnit) {
      const newHash = utils.updateHashPart('unit', newUnit.id);
      $.history.load(newHash);
      this.setOffset(newUnit.id);
    } else if (opts.isSubmission) {
      cookie('finished', '1', { path: '/' });
      window.location.href = this.backToBrowserEl.getAttribute('href');
    }
    return true;
  },


  /* Loads the editor with a specific unit */
  gotoUnit(e) {
    e.preventDefault();

    if (!PTL.editor.canNavigate()) {
      return false;
    }

    // Ctrl + click / Alt + click / Cmd + click / Middle click opens a new tab
    if (e.ctrlKey || e.altKey || e.metaKey || e.which === 2) {
      const $el = e.target.nodeName !== 'TD' ?
                  $(e.target).parents('td') :
                  $(e.target);
      window.open($el.data('target'), '_blank');
      return false;
    }

    // Don't load anything if we're just selecting text
    if (window.getSelection().toString() !== '') {
      return false;
    }

    // Get clicked unit's uid from the row's id information and
    // try to load it
    const m = this.id.match(/(row|ctx)([0-9]+)/);
    if (m) {
      const type = m[1];
      const uid = parseInt(m[2], 10);
      let newHash;
      if (type === 'row') {
        newHash = utils.updateHashPart('unit', uid);
      } else {
        newHash = `unit=${encodeURIComponent(uid)}`;
      }
      $.history.load(newHash);
      PTL.editor.setOffset(uid);
    }
    return true;
  },

  /* Selects the element's contents and sets the focus */
  unitIndex(e) {
    e.preventDefault();

    const selection = window.getSelection();
    const range = document.createRange();

    range.selectNodeContents(this.unitIndexEl);
    selection.removeAllRanges();
    selection.addRange(range);
    this.unitIndexEl.focus();
  },

  /* Loads the editor on a index */
  gotoIndex(e) {
    if (e.which !== 13) { // Enter key
      return;
    }

    e.preventDefault();
    const index = parseInt(this.unitIndexEl.textContent, 10) - 1;
    if (isNaN(index)) {
      return;
    }

    // if index is outside of current uids clear units first
    if (index < this.initialOffset || index >= this.getOffsetOfLastUnit()) {
      this.initialOffset = -1;
      this.offset = 0;
      this.offsetRequested = index + 1;
      const newHash = utils.updateHashPart('offset',
                                           this.getStartOfChunk(index),
                                           ['unit']);
      $.history.load(newHash);
    } else if (index >= 0 && index <= this.units.total) {
      const uId = this.units.uIds[(index - this.initialOffset)];
      const newHash = utils.updateHashPart('unit', uId);
      $.history.load(newHash);
    }
  },

  /*
   * Units filtering
   */

  /* Gets the failing check options for the current query */
  getCheckOptions() {
    StatsAPI.getChecks(this.settings.pootlePath)
      .then(
        (data) => this.appendChecks(data),
        this.error
      );
  },

  /* Loads units based on checks filtering */
  filterChecks() {
    if (this.preventNavigation) {
      return false;
    }
    if (!this.canNavigate()) {
      return false;
    }

    const filterChecks = this.$filterChecks.val();

    if (filterChecks !== 'none') {
      const sortBy = this.$filterSortBy.val();
      const newHash = {
        filter: 'checks',
        checks: filterChecks,
      };

      if (sortBy !== 'default') {
        newHash.sort = sortBy;
      }

      $.history.load($.param(newHash));
    }
    return true;
  },

  /* Adds the failing checks to the UI */
  appendChecks(checks) {
    if (Object.keys(checks).length) {
      const $checks = this.$filterChecks;
      const selectedValue = this.checks[0] || 'none';

      $checks.find('optgroup').each(function displayGroups() {
        const $gr = $(this);
        let empty = true;

        $gr.find('option').each(function displayOptions() {
          const $opt = $(this);
          const value = $opt.val();

          if (value in checks) {
            empty = false;
            $opt.text(`${$opt.data('title')}(${checks[value]})`);
          } else {
            $opt.remove();
          }
        });

        if (empty) {
          $gr.hide();
        }
      });

      $checks.select2(filterSelectOpts).select2('val', selectedValue);
      this.$filterChecksWrapper.css('display', 'inline-block');
    } else { // No results
      this.displayMsg({ body: gettext('No results.') });
      this.$filterStatus.select2('val', this.filter);
    }
  },

  filterSort() {
    const filterBy = this.$filterStatus.val();
    // #104: Since multiple values can't be selected in the select
    // element, we also need to check for `this.checks`.
    const filterChecks = this.$filterChecks.val() || this.checks.join(',');
    const sortBy = this.$filterSortBy.val();
    const user = this.user || null;

    const newHash = { filter: filterBy };

    if (this.category.length) {
      newHash.category = this.category;
    } else if (filterChecks !== 'none') {
      newHash.checks = filterChecks;
    }

    if (sortBy !== 'default') {
      newHash.sort = sortBy;
    }
    if (user !== null) {
      newHash.user = user;
    }

    $.history.load($.param(newHash));
  },


  /* Loads units based on filtering */
  filterStatus() {
    if (!this.canNavigate()) {
      return false;
    }

    // this function can be executed in different contexts,
    // so using the full selector here
    const $selected = this.$filterStatus.find('option:selected');
    const filterBy = $selected.val();

    if (filterBy === 'checks') {
      this.getCheckOptions();
    } else { // Normal filtering options (untranslated, fuzzy...)
      this.$filterChecksWrapper.hide();

      if (!this.preventNavigation) {
        const newHash = { filter: filterBy };
        const isUserFilter = $selected.data('user');

        if (this.user && isUserFilter) {
          newHash.user = this.user;
        } else {
          this.user = null;
          $('.js-user-filter').remove();

          if (this.sortBy !== 'default') {
            newHash.sort = this.sortBy;
          }
        }

        $.history.load($.param(newHash));
      }
    }
    return true;
  },

  /* Generates the edit context rows' UI */
  renderCtxControls({ hasData = false }) {
    const ctxRowBefore = this.tmpl.editCtx({
      hasData,
      extraCls: 'before',
    });
    const ctxRowAfter = this.tmpl.editCtx({
      hasData,
      extraCls: 'after',
    });

    return [ctxRowBefore, ctxRowAfter];
  },

  replaceCtxControls(ctx) {
    const [ctxRowBefore, ctxRowAfter] = ctx;

    $('tr.edit-ctx.before').replaceWith(ctxRowBefore);
    $('tr.edit-ctx.after').replaceWith(ctxRowAfter);
  },

  handleContextSuccess(data) {
    if (!data.ctx.before.length && !data.ctx.after.length) {
      return undefined;
    }

    // As we now have got more context rows, increase its gap
    this.ctxGap += Math.max(data.ctx.before.length,
                            data.ctx.after.length);
    cookie('ctxQty', this.ctxGap, { path: '/' });

    // Create context rows HTML
    const before = this.renderCtxRows(data.ctx.before, 'before');
    const after = this.renderCtxRows(data.ctx.after, 'after');

    // Append context rows to their respective places
    const editCtxRows = $('tr.edit-ctx');
    editCtxRows.first().after(before);
    editCtxRows.last().before(after);
    return undefined;
  },

  /* Gets more context units */
  moreContext(amount = CTX_STEP) {
    return (
      UnitAPI.getContext(this.units.getCurrent().id,
                         { gap: this.ctxGap, qty: amount })
        .then(
          (data) => this.handleContextSuccess(data),
          this.error
        )
    );
  },

  /* Shrinks context lines */
  lessContext() {
    const $before = $('.ctx-row.before');
    const $after = $('.ctx-row.after');

    // Make sure there are context rows before decreasing the gap and
    // removing any context rows
    if ($before.length || $after.length) {
      if ($before.length === this.ctxGap) {
        $before.slice(0, CTX_STEP).remove();
      }

      if ($after.length === this.ctxGap) {
        $after.slice(-CTX_STEP).remove();
      }

      this.ctxGap -= CTX_STEP;

      if (this.ctxGap >= 0) {
        if (this.ctxGap === 0) {
          this.replaceCtxControls(this.renderCtxControls({ hasData: false }));
        }

        cookie('ctxQty', this.ctxGap, { path: '/' });
      }
    }
  },

  /* Shows context rows */
  showContext() {
    const $before = $('.ctx-row.before');
    const $after = $('.ctx-row.after');

    if ($before.length || $after.length) {
      $before.show();
      $after.show();
      this.replaceCtxControls(this.renderCtxControls({ hasData: true }));
    } else if (this.ctxQty > 0) {
      // This is an initial request for context, reset `ctxGap`
      this.ctxGap = 0;
      this.moreContext(this.ctxQty)
          .then(() => {
            this.replaceCtxControls(this.renderCtxControls({ hasData: true }));
          });
    }
  },

  /* Hides context rows */
  hideContext() {
    const $before = $('.ctx-row.before');
    const $after = $('.ctx-row.after');

    $before.hide();
    $after.hide();

    this.replaceCtxControls(this.renderCtxControls({ hasData: false }));
  },


  /* Loads the search view */
  onSearch(searchText) {
    if (!PTL.editor.canNavigate()) {
      return false;
    }

    let newHash;

    if (searchText) {
      const queryString = this.buildSearchQuery();
      newHash = `search=${queryString}`;
    } else {
      newHash = utils.updateHashPart('filter', 'all', ['search', 'sfields', 'soptions']);
    }
    $.history.load(newHash);
    return true;
  },


  /*
   * Comments
   */

  addComment(e) {
    e.preventDefault();
    this.updateCommentDefaultProperties();

    UnitAPI.addComment(this.units.getCurrent().id, $(e.target).serializeObject())
      .then(
        (data) => this.processAddComment(data),
        this.error
      );
  },

  processAddComment(data) {
    $('.js-editor-comment').removeClass('selected');
    $('#editor-comment').fadeOut(200);

    if ($('#translator-comment').length) {
      $(data.comment).hide().prependTo('#translator-comment').delay(200)
        .animate({ height: 'show' }, 1000, 'easeOutQuad');
    } else {
      $(`<div id='translator-comment'>${data.comment}</div>`)
        .prependTo('#extras-container').delay(200)
        .hide().animate({ height: 'show' }, 1000, 'easeOutQuad');
    }

    helpers.updateRelativeDates();
  },

  /* Removes last comment */
  removeComment(e) {
    e.preventDefault();

    UnitAPI.removeComment(this.units.getCurrent().id)
      .then(
        () => $('.js-comment-first').fadeOut(200),
        this.error
      );
  },


  /*
   * Unit timeline
   */

  /* Get the timeline data */
  showTimeline() {
    const $results = $('#timeline-results');
    if ($results.length) {
      $results.slideDown(1000, 'easeOutQuad');
      return;
    }

    const $node = $('.translate-container');
    $node.spin();

    UnitAPI.getTimeline(this.units.getCurrent().id)
      .then(
        (data) => this.renderTimeline(data),
        this.error
      )
      .always(() => $node.spin(false));
  },

  renderTimeline(data) {
    const uid = data.uid;

    if (data.timeline && uid === this.units.getCurrent().id) {
      if ($('#translator-comment').length) {
        $(data.timeline).hide().insertAfter('#translator-comment')
                        .slideDown(1000, 'easeOutQuad');
      } else {
        $(data.timeline).hide().prependTo('#extras-container')
                        .slideDown(1000, 'easeOutQuad');
      }
      [...document.querySelectorAll('.js-mount-timesince')].forEach((el, i) => {
        const props = {
          title: data.entries_group[i].display_datetime,
          dateTime: data.entries_group[i].iso_datetime,
        };
        if (data.entries_group[i].via_upload) {
          ReactRenderer.render(<UploadTimeSince {...props} />, el);
        } else {
          ReactRenderer.render(<TimeSince {...props} />, el);
        }
      });

      $('.timeline-field-body').filter(':not([dir])').bidi();
      $('#js-show-timeline').addClass('selected');
    }
  },

  /* Hide the timeline panel */
  toggleTimeline(e) {
    e.preventDefault();
    const $timelineToggle = $('#js-toggle-timeline');
    $timelineToggle.toggleClass('selected');
    if ($timelineToggle.hasClass('selected')) {
      this.showTimeline();
    } else {
      $('#timeline-results').slideUp(1000, 'easeOutQuad');
    }
  },


  /*
   * User and TM suggestions
   */

  /* Filters TM results and does some processing */
  filterTMResults(results, sourceText) {
    // FIXME: this just retrieves the first three results
    // we could limit based on a threshold too.
    const filtered = [];

    // FIXME: move this side-effect elsewhere
    if (results.length > 0 && results[0].source === sourceText) {
      const $element = $(this.focused);
      // set only if the textarea is empty
      if ($element.val() === '') {
        // save unit editor state to restore it after autofill changes
        const isUnitDirty = PTL.editor.isUnitDirty;
        const text = results[0].target;
        $element.val(text).trigger('input');
        $element.caret(text.length, text.length);
        this.goFuzzy();
        PTL.editor.isUnitDirty = isUnitDirty;
      }
    }

    for (let i = 0; i < results.length && i < 3; i++) {
      const result = results[i];
      let fullname = result.fullname;
      if (result.username === 'nobody') {
        fullname = gettext('some anonymous user');
      } else if (!result.fullname) {
        fullname = result.username ? result.username : gettext('someone');
      }
      result.fullname = _.escape(fullname);
      result.project = _.escape(result.project);
      result.path = _.escape(result.path);

      filtered.push(result);
    }

    return filtered;
  },

  /* TM suggestions */
  getTMUnitsContent(data) {
    const unit = this.units.getCurrent();
    const store = unit.get('store');
    const sourceText = unit.get('source')[0];
    const filtered = this.filterTMResults(data, sourceText);
    const name = gettext('Similar translations');

    if (filtered.length) {
      return this.tmpl.tm({
        name,
        store: store.toJSON(),
        unit: unit.toJSON(),
        suggs: filtered,
      });
    }

    return '';
  },

  /* Gets TM suggestions from amaGama */
  getTMUnits() {
    const unit = this.units.getCurrent();
    const store = unit.get('store');
    const src = store.get('source_lang');
    const tgt = store.get('target_lang');
    const sText = unit.get('source')[0];

    if (!sText.length || src === tgt) {
      return;
    }

    const pStyle = store.get('project_style');
    let tmUrl = `${this.settings.tmUrl}${src}/${tgt}/unit/` +
      `?source=${encodeURIComponent(sText)}`;

    if (pStyle.length && pStyle !== 'standard') {
      tmUrl += `&style=${pStyle}`;
    }

    fetch({ url: tmUrl, crossDomain: true })
      .then(
        (data) => this.handleTmResults(data, store, unit),
        (xhr, s) => console.error(`HTTP ${xhr.status} (${s}): ${tmUrl}`)
      );
  },

  handleTmResults(data, store, unit) {
    if (!data.length) {
      return false;
    }

    const sourceText = unit.get('source')[0];
    const filtered = PTL.editor.filterTMResults(data, sourceText);
    const name = gettext('Similar translations');
    const tm = PTL.editor.tmpl.tm({
      name,
      store: store.toJSON(),
      unit: unit.toJSON(),
      suggs: filtered,
    });

    $(tm).hide().appendTo('#extras-container')
                .slideDown(1000, 'easeOutQuad');
    return true;
  },


  /* Rejects a suggestion */
  handleRejectSuggestion(suggId, { requestData = {} } = {}) {
    this.rejectSuggestion(suggId, { requestData });
  },

  rejectSuggestion(suggId, { requestData = {} } = {}) {
    UnitAPI.rejectSuggestion(this.units.getCurrent().id, suggId, requestData)
      .then(
        (data) => this.processRejectSuggestion(data, suggId),
        this.error
      );
  },

  processRejectSuggestion(data, suggId) {
    if (data.user_score) {
      score.set(data.user_score);
    }

    $(`#suggestion-${suggId}`).fadeOut(200, function handleRemove() {
      PTL.editor.closeSuggestion({ checkIfCanNavigate: false });
      $(this).remove();

      // Go to the next unit if there are no more suggestions left
      if (!$('.js-user-suggestion').length) {
        PTL.editor.gotoNext();
      }
    });
  },


  /* Accepts a suggestion */
  handleAcceptSuggestion(
    suggId, { requestData = {}, isSuggestionChanged = false } = {}
  ) {
    if (isSuggestionChanged) {
      const area = document.querySelector('.js-translation-area');
      area.value = decodeEntities(requestData.translation);
      this.undoFuzzyBox();
      this.handleSubmit(requestData.comment);
    } else {
      this.acceptSuggestion(suggId, { requestData });
    }
  },

  acceptSuggestion(suggId, { requestData = {}, skipToNext = false } = {}) {
    UnitAPI.acceptSuggestion(this.units.getCurrent().id, suggId, requestData)
    .then(
      (data) => this.processAcceptSuggestion(data, suggId, skipToNext),
      this.error
    );
  },

  processAcceptSuggestion(data, suggId, skipToNext) {
    // Update target textareas
    if (data.newtargets !== undefined) {
      $.each(data.newtargets, (i, target) => {
        $(`#id_target_f_${i}`).val(target).focus();
      });
    }

    if (data.newdiffs !== undefined) {
      // Update remaining suggestion's diff
      $.each(data.newdiffs, (suggestionId, sugg) => {
        $.each(sugg, (i, target) => {
          $(`#suggdiff-${suggestionId}-${i}`).html(target);
        });
      });
    }

    // FIXME: handle this via events
    const translations = $('.js-translation-area').map((i, el) => $(el).val())
                                                  .get();
    const unit = this.units.getCurrent();
    unit.setTranslation(translations);
    unit.set('isfuzzy', false);

    if (data.user_score) {
      score.set(data.user_score);
    }

    const hasCriticalChecks = !!data.checks;
    $('.translate-container').toggleClass('error', hasCriticalChecks);
    if (hasCriticalChecks) {
      _refreshChecksSnippet(data.checks);
    }

    $(`#suggestion-${suggId}`).fadeOut(200, function handleRemove() {
      PTL.editor.closeSuggestion({ checkIfCanNavigate: false });
      $(this).remove();

      // Go to the next unit if there are no more suggestions left,
      // provided there are no critical failing checks
      if (!hasCriticalChecks && (skipToNext || !$('.js-user-suggestion').length)) {
        PTL.editor.gotoNext();
      }
    });
  },

  /* Mutes or unmutes a quality check marking it as false positive or not */
  toggleCheck(checkId) {
    const $check = $(`.js-check-${checkId}`);
    const isFalsePositive = !$check.hasClass('false-positive');

    UnitAPI.toggleCheck(this.units.getCurrent().id, checkId,
                        { mute: isFalsePositive })
      .then(
        () => this.processToggleCheck(checkId, isFalsePositive),
        this.error
      );
  },

  processToggleCheck(checkId, isFalsePositive) {
    $(`.js-check-${checkId}`).toggleClass('false-positive', isFalsePositive);

    const hasError = $('#translate-checks-block .check')
      .not('.false-positive').size() > 0;

    $('.translate-container').toggleClass('error', hasError);
  },

  /*
   * Machine Translation
   */

  runHooks() {
    mtProviders.forEach((provider) => provider.init({
      unit: this.units.getCurrent().toJSON(),
    }));
  },

  /* FIXME: provide an alternative to such an ad-hoc entry point */
  setTranslation(opts) {
    const { translation } = opts;
    if (translation === undefined && opts.msg) {
      this.displayError(opts.msg);
      return false;
    }

    const area = document.querySelector('.js-translation-area');

    area.value = decodeEntities(translation);
    autosize.update(area);

    // Save a copy of the resulting text in the DOM for further
    // similarity comparisons
    area.dataset.translationAidMt = translation;

    area.dispatchEvent((new Event('input')));
    area.focus();

    this.goFuzzy();

    return true;
  },

  toggleSuggestion(e, { canHide = false } = {}) {
    e.stopPropagation();
    const suggestionId = parseInt(e.currentTarget.dataset.suggId, 10);
    const suggestion = document.getElementById(`suggestion-${suggestionId}`);

    if (this.selectedSuggestionId === undefined) {
      this.selectedSuggestionId = suggestionId;
      const props = {
        suggId: this.selectedSuggestionId,
        initialSuggestionText: e.currentTarget.dataset.translationAid,
        localeDir: this.settings.localeDir,
        onAcceptSuggestion: this.handleAcceptSuggestion.bind(this),
        onRejectSuggestion: this.handleRejectSuggestion.bind(this),
        onChange: this.handleSuggestionFeedbackChange.bind(this),
      };
      const mountSelector = `.js-mnt-suggestion-feedback-${suggestionId}`;
      const feedbackMountPoint = document.querySelector(mountSelector);
      const editorBody = document.querySelector('.js-editor-body .translate-full');
      suggestion.classList.add('suggestion-expanded');
      editorBody.classList.add('suggestion-expanded');

      this.isSuggestionFeedbackFormDirty = false;
      this.suggestionFeedbackForm = ReactDOM.render(
        <SuggestionFeedbackForm {...props} />,
        feedbackMountPoint
      );
    } else if (canHide) {
      this.closeSuggestion();
    }
  },

  handleSuggestionFeedbackChange(isDirty) {
    this.isSuggestionFeedbackFormDirty = isDirty;
  },

  closeSuggestion({ checkIfCanNavigate = true } = {}) {
    if (this.selectedSuggestionId !== undefined &&
        (!checkIfCanNavigate || this.canNavigate())) {
      const suggestion = document.querySelector(`#suggestion-${this.selectedSuggestionId}`);
      const editorBody = document.querySelector('.js-editor-body .translate-full');
      const mountSelector = `.js-mnt-suggestion-feedback-${this.selectedSuggestionId}`;
      const feedbackMountPoint = document.querySelector(mountSelector);
      editorBody.classList.remove('suggestion-expanded');
      suggestion.classList.remove('suggestion-expanded');
      ReactDOM.unmountComponentAtNode(feedbackMountPoint);
      this.selectedSuggestionId = undefined;
      this.suggestionFeedbackForm = undefined;
      this.isSuggestionFeedbackFormDirty = false;
    }
  },
};
