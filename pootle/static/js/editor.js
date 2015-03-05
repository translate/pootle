(function ($) {

  window.PTL = window.PTL || {};

  PTL.editor = {

  /* Initializes the editor */
  init: function (options) {

    /* Default settings */
    this.settings = {
      mt: []
    };

    options && $.extend(this.settings, options);

    /* Initialize variables */
    this.units = new PTL.collections.UnitCollection;

    this.pager = {current: 1};
    this.pagesGot = {};

    this.filter = 'all';
    this.checks = [];
    this.goal = null;
    this.user = null;
    this.ctxGap = 0;
    this.ctxQty = parseInt($.cookie('ctxQty'), 10) || 1;
    this.ctxStep= 1;
    this.keepState = false;
    this.preventNavigation = false;

    this.isLoading = true;
    this.showActivity();

    /* Currently active search fields */
    this.searchFields = [];
    this.searchOptions = [];

    /* Regular expressions */
    this.cpRE = /^(<[^>]+>|\[n\|t]|\W$^\n)*(\b|$)/gm;

    /* Timeline requests handler */
    this.timelineReq = null;

    /* TM requests handler */
    this.tmReq = null;

    /* Differencer */
    this.differencer = new diff_match_patch();

    /* Compile templates */
    this.tmpl = {vUnit: _.template($('#view_unit').html()),
                 tm: _.template($('#tm_suggestions').html()),
                 editCtx: _.template($('#editCtx').html())}

    /* Initialize search */
    // TODO: pass the environment option to the init
    PTL.search.init({
      onSubmit: this.search
    });

    /*
     * Bind event handlers
     */

    /* Captcha */
    $(document).on('submit', '#captcha', function (e) {
      e.preventDefault();
      var fn = $(this).data('js-action');
      PTL.editor[fn](e);
      $.magnificPopup.close();
    });

    /* Fuzzy / unfuzzy */
    $(document).on('keyup blur', 'textarea.translation', function () {
      if (!PTL.editor.keepState &&
          $(this).prop('defaultValue') !== $(this).val()) {
        PTL.editor.ungoFuzzy();
      }
    });
    $(document).on('click', 'input.fuzzycheck', function () {
      if (PTL.editor.isFuzzy()) {
        PTL.editor.doFuzzyArea();
      } else {
        PTL.editor.undoFuzzyArea();
      }
    });

    /* Suggest / submit */
    $(document).on('click', '.switch-suggest-mode a', function () {
      PTL.editor.toggleSuggestMode();
      return false;
    });

    /* Update focus when appropriate */
    $(document).on('focus', '.focusthis', function (e) {
      PTL.editor.focused = e.target;
    });

    /* Write TM results, special chars... into the currently focused element */
    $(document).on('click', '.js-editor-copytext', this.copyText);

    /* Copy original translation */
    $(document).on('click', '.js-copyoriginal', function () {
      PTL.editor.copyOriginal($('.translation-text',
        $(this).parent().parent().parent()));
    });

    /* Copy suggestion */
    $(document).on('click', 'div.suggestion', function () {
      // Don't copy if text has been selected
      if (PTL.editor.getSelectedText()) {
        return;
      }
      if ($('#id_target_f_0').attr('disabled')) {
        return;
      }
      PTL.editor.copyOriginal($('.suggestion-translation', this));
    });

    /* Editor navigation/submission */
    $(document).on('editor_ready', 'table.translate-table', this.ready);
    $(document).on('noResults', 'table.translate-table', this.noResults);
    $(document).on('mouseup', 'tr.view-row, tr.ctx-row', this.gotoUnit);
    $(document).on('keypress', '#item-number', function (e) {
      // Perform action only when the 'Enter' key is pressed
      if (e.which === 13) {
        PTL.editor.gotoIndex(parseInt($('#item-number').val(), 10));
      }
    });
    $(document).on('click', 'input.submit', this.submit);
    $(document).on('click', 'input.suggest', this.suggest);
    $(document).on('click', '#js-nav-prev, #js-nav-next', this.gotoPrevNext);
    $(document).on('click', '.js-suggestion-reject', this.rejectSuggestion);
    $(document).on('click', '.js-suggestion-accept', this.acceptSuggestion);
    $(document).on('click', '.js-vote-clear', this.clearVote);
    $(document).on('click', '.js-vote-up', this.voteUp);
    $(document).on('click', '#js-show-timeline', this.showTimeline);
    $(document).on('click', '#js-hide-timeline', this.hideTimeline);
    $(document).on('click', '#translate-checks-block .js-reject-check', this.rejectCheck);

    /* Filtering */
    $(document).on('change', '#filter-status select', this.filterStatus);
    $(document).on('change', '#filter-checks select', this.filterChecks);
    $(document).on('click', '.js-more-ctx', function () {
      PTL.editor.moreContext(false);
    });
    $(document).on('click', '.js-less-ctx', this.lessContext);
    $(document).on('click', '.js-show-ctx', this.showContext);
    $(document).on('click', '.js-hide-ctx', this.hideContext);

    /* Commenting */
    $(document).on('click', '.js-editor-comment', function (e) {
      e.preventDefault();
      $('#editor-comment').slideToggle('fast');
    });
    $(document).on('submit', '#comment-form', this.comment);

    /* Misc */
    $(document).on('click', '.js-editor-msg-hide', this.hideMsg);

    /* Bind hotkeys */
    shortcut.add('ctrl+return', function () {
      if (PTL.editor.isSuggestMode()) {
        $('input.suggest').trigger('click');
      } else {
        $('input.submit').trigger('click');
      }
    });
    shortcut.add('ctrl+space', function (e) {
      // To prevent the click event which occurs in Firefox
      // but not in Chrome (and not in IE)
      if (e && e.preventDefault) {
        e.preventDefault();
      }

      // Prevent automatic unfuzzying on keyup
      PTL.editor.keepState = true;

      if (PTL.editor.isFuzzy()) {
        PTL.editor.ungoFuzzy();
      } else {
        PTL.editor.goFuzzy();
      }
    });
    shortcut.add('ctrl+shift+space', function () {
      PTL.editor.toggleSuggestMode();
    });

    shortcut.add('ctrl+up', function () {
      $('#js-nav-prev').trigger('click');
    });
    shortcut.add('ctrl+,', function () {
      $('#js-nav-prev').trigger('click');
    });

    shortcut.add('ctrl+down', function () {
      $('#js-nav-next').trigger('click');
    });
    shortcut.add('ctrl+.', function () {
      $('#js-nav-next').trigger('click');
    });

    if (navigator.platform.toUpperCase().indexOf('MAC') >= 0) {
      // Optimize string join with '<br/>' as separator
      $('#js-nav-next')
        .attr('title',
              gettext(['Go to the next string (Ctrl+.)', '',
                       'Also:', 'Next page: Ctrl+Shift+.',
                       'Last page: Ctrl+Shift+End'].join('<br/>'))
      );
      $('#js-nav-prev')
        .attr('title',
              gettext(['Go to the previous string (Ctrl+,)', '',
                       'Also:', 'Previous page: Ctrl+Shift+,',
                       'First page: Ctrl+Shift+Home'].join('<br/>'))
      );
    }
    
    shortcut.add('ctrl+shift+n', function () {
      $('#item-number').focus().select();
    });

    /* XHR activity indicator */
    $(document).ajaxStart(function () {
      clearTimeout(PTL.editor.delayedActivityTimer);
      PTL.editor.delayedActivityTimer = setTimeout(function () {
        PTL.editor.showActivity();
      }, 3000);
    });
    $(document).ajaxStop(function () {
      clearTimeout(PTL.editor.delayedActivityTimer);
      if (!PTL.editor.isLoading) {
        PTL.editor.hideActivity();
      }
    });

    /* Load MT backends */
    $.each(this.settings.mt, function () {
      var backend = this.name, key = this.key;

      $.ajax({
        url: s(['js/mt/', backend, '.js'].join('')),
        async: false,
        dataType: 'script',
        success: function () {
          setTimeout(function () {
            PTL.editor.mt[backend].init(key);
          }, 0);
          $(document).on('mt_ready', 'table.translate-table',
                         PTL.editor.mt[backend].ready);
        }
      });
    });

    /* Load lookup backends */
    $.each(this.settings.lookup, function () {
      var backend = this;

      $.ajax({
        url: s(['js/lookup/', backend, '.js'].join('')),
        async: false,
        dataType: 'script',
        success: function () {
          setTimeout(function () {
            PTL.editor.lookup[backend].init();
          }, 0);
          $(document).on('lookup_ready', 'table.translate-table',
                         PTL.editor.lookup[backend].ready);
        }
      });
    });

    // Update relative dates every minute
    setInterval(PTL.common.updateRelativeDates, 6e4);

    /* History support */
    setTimeout(function () {
      $.history.init(function (hash) {
        var params = PTL.utils.getParsedHash(hash),
            withUid = 0,
            tmpParamValue;

        // Walk through known filtering criterias and apply them to the editor object

        if (params['unit']) {
          tmpParamValue = parseInt(params['unit'], 10);

          if (tmpParamValue && !isNaN(tmpParamValue)) {
            var current = PTL.editor.units.getCurrent(),
                newUnit = PTL.editor.units.get(tmpParamValue);
            if (newUnit && newUnit !== current) {
              PTL.editor.units.setCurrent(newUnit);
              PTL.editor.displayEditUnit();
              return;
            } else {
              withUid = tmpParamValue;
            }
          }
        }

        PTL.editor.pager.current = 1;
        PTL.editor.filter = 'all';

        if ('filter' in params) {
          var filterName = params['filter'];

          // Set current state
          PTL.editor.filter = filterName;

          if (filterName === 'checks' && 'checks' in params) {
            PTL.editor.checks = params['checks'].split(',');
          } else {
            PTL.editor.checks = [];
          }
        }

        PTL.editor.goal = null;
        if ('goal' in params) {
          PTL.editor.goal = params['goal'];
        }

        // Only accept the user parameter for 'user-*' filters
        if ('user' in params && PTL.editor.filter.indexOf('user-') === 0) {
          var user;
          PTL.editor.user = user = encodeURIComponent(params.user);

          var newOpts = [],
              values = {
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
              // Translators: '%s' is a username, meaning "submissions by %s, that were overwritten"
              interpolate(gettext("%s's overwritten submissions"), [user]),
          };
          for (var key in values) {
            newOpts.push([
              '<option value="', key, '" data-user="', user, '" class="',
              'js-user-filter' ,'">', values[key], '</option>'
            ].join(''));
          }
          $(".js-user-filter").remove();
          $('#filter-status select').append(newOpts.join(''))
        }

        if ('search' in params) {
          // Note that currently the search, if provided along with the other
          // filters, would override them
          PTL.editor.filter = "search";
          PTL.editor.searchText = params['search'];
          if ('sfields' in params) {
            PTL.editor.searchFields = params['sfields'].split(',');
          }
          PTL.editor.searchOptions = [];
          if ('soptions' in params) {
             PTL.editor.searchOptions = params['soptions'].split(',');
          }
        }

        // Update the filter UI to match the current filter

        // disable navigation on UI toolbar events to prevent data reload
        PTL.editor.preventNavigation = true;

        $('#filter-status select').select2('val', PTL.editor.filter);
        if (PTL.editor.filter == "checks") {
          // if the checks selector is empty (i.e. the 'change' event was not fired
          // because the selection did not change), force the update to populate the selector
          if (!$("#filter-checks").length) {
            PTL.editor.filterStatus();
          }
          $('#filter-checks select').select2('val', PTL.editor.checks[0]);
        }

        if (PTL.editor.filter == "search") {
          $("#id_search").val(PTL.editor.searchText);
          $("#id_search").trigger('focus');

          // Set defaults if no fields have been specified
          if (!PTL.editor.searchFields.length) {
            PTL.editor.searchFields = ["source", "target"];
          }

          $(".js-search-fields input").each(function () {
            if ($.inArray($(this).val(), PTL.editor.searchFields) >= 0) {
              $(this).attr("checked", "checked");
            } else {
              $(this).removeAttr("checked");
            }
          });

          $(".js-search-options input").each(function () {
            if ($.inArray($(this).val(), PTL.editor.searchOptions) >= 0) {
              $(this).attr("checked", "checked");
            } else {
              $(this).removeAttr("checked");
            }
          });

          // Remove any possible applied checks
          $('#filter-checks').remove();
        }

        // re-enable normal event handling
        PTL.editor.preventNavigation = false;

        // Load the units that match the given criterias
        PTL.editor.getViewUnits({pager: true, withUid: withUid});

        if (PTL.editor.hasResults) {
          // ensure all the data is preloaded before rendering the table
          // otherwise, when the page is reloaded, some pages will not yet be there
          PTL.editor.fetchPages({async: false});

          if (PTL.editor.units.getCurrent() === undefined) {
            PTL.editor.units.setFirstAsCurrent();
          }
          PTL.editor.displayEditUnit();
        }

      }, {'unescape': true});
    }, 1); // not sure why we had a 1000ms timeout here

  },

  /* Stuff to be done when the editor is ready  */
  ready: function () {
    // Set textarea's initial height as well as the max-height
    var maxheight = $(window).height() * 0.3;
    $('textarea.expanding').TextAreaExpander('10', maxheight);

    // set direction of the comment body
    $('.extra-item-comment').filter(':not([dir])').bidi();
    // set direction of the suggestion body
    $('.suggestion-translation-body').filter(':not([dir])').bidi();

    // Focus on the first textarea, if any
    if ($(".focusthis").get(0)) {
      $(".focusthis").get(0).focus();
    }

    PTL.editor.settings.targetLang = PTL.editor.normalizeCode($(".translate-translation textarea").attr("lang"));

    PTL.editor.hlSearch();

    if (PTL.editor.settings.tmUrl != '') {
      PTL.editor.getTMUnits();
    }

    // All is ready, let's call the ready functions of the MT backends
    $("table.translate-table").trigger("mt_ready");
    $("table.translate-table").trigger("lookup_ready");

    PTL.editor.isLoading = false;
    PTL.editor.hideActivity();
    PTL.editor.updateExportLink();
    PTL.common.updateRelativeDates();

    // clear any pending 'Loading...' indicator timer
    // as ajaxStop() is not fired in IE properly
    // at initial page load (?!)
    clearTimeout(PTL.editor.delayedActivityTimer);
  },

  /* Things to do when no results are returned */
  noResults: function () {
    PTL.editor.displayMsg(gettext("No results."));
    PTL.editor.reDraw(false);
  },


  /*
   * Text utils
   */

  /* Escape unsafe regular expression symbols:
   * ! $ & ( ) * + - . : < = > ? [ \ ] ^ { | }
   *
   * Special characters can be written as
   * Regular Expression class:
   * [!$&(-+\-.:<-?\[-^{-}]
   */
  escapeUnsafeRegexSymbols: function (s) {
    // Replace doesn't modify original variable and it recreates a
    // new string with special characters escaped.
    return s.replace(/[!$&(-+\-.:<-?\[-^{-}]/g, '\\$&');
  },

  /* Make regular expression using every word
   * in input string
   */
  makeRegexForMultipleWords: function (s) {
    // This function has these steps:
    // 1) escape unsafe regular expression symbols;
    // 2) trim ' ' (whitespaces) to avoid multiple
    //    '|' at the beginning and at the end;
    // 3) replace ' ' (one or more whitespaces) with '|'. In this
    //    way every word can be searched by regular expression;
    // 4) add brackets.
    return ['(', PTL.editor.escapeUnsafeRegexSymbols(s).trim().replace(/ +/g,
      '|'), ')'].join('');
  },

  /* Highlights search results */
  hlSearch: function () {
    var hl = PTL.editor.filter == "search" ? PTL.editor.searchText : "",
        sel = [],
        selMap = {
          notes: 'div.developer-comments',
          locations: 'div.translate-locations',
          source: 'td.translate-original, div.original div.translation-text',
          target: 'td.translate-translation'
        },
        hlRegex;

    // Build highlighting selector based on chosen search fields
    $.each(PTL.editor.searchFields, function (i, field) {
      sel.push("tr.edit-row " + selMap[field]);
      sel.push("tr.view-row " + selMap[field]);
    });

    if (PTL.editor.searchOptions.indexOf('exact') >= 0 ) {
      hlRegex = new RegExp([
          '(', PTL.editor.escapeUnsafeRegexSymbols(hl), ')'
        ].join(''));
    } else {
      hlRegex = new RegExp(PTL.editor.makeRegexForMultipleWords(hl), "i");
    }
    $(sel.join(", ")).highlightRegex(hlRegex);
  },


  /* Copies text into the focused textarea */
  copyText: function (e) {
    var selector, text, element, start,
        action = $(this).data('action');

    // Determine which text we need
    selector = $(".tm-translation", this).ifExists() ||
               $(".suggestion-translation", this).ifExists() || $(this);
    text = selector.data('entity') || selector.text();

    element = $(PTL.editor.focused);

    if (action === "overwrite") {
      element.val(text);
      start = text.length;
    } else {
      start = element.caret().start + text.length;
      element.val(element.caret().replace(text));
    }

    element.caret(start, start);
  },


  /* Copies source text(s) into the target textarea(s)*/
  copyOriginal: function (sources) {
    var cleanSources = [];
    $.each(sources, function (i) {
      cleanSources[i] = $(this).text();
    });

    var targets = $("[id^=id_target_f_]");
    if (targets.length) {
      var i, active,
          max = cleanSources.length - 1;

      for (var i=0; i<targets.length; i++) {
        var newval = cleanSources[i] || cleanSources[max];
        $(targets.get(i)).val(newval);
      }

      // Focus on the first textarea
      active = $(targets).get(0);
      active.focus();
      // Make this fuzzy
      PTL.editor.goFuzzy();
      // Place cursor at start of target text
      PTL.editor.cpRE.exec($(active).val());
      i = PTL.editor.cpRE.lastIndex;
      $(active).caret(i, i);
      PTL.editor.cpRE.lastIndex = 0;
    }
  },


  /* Gets selected text */
  getSelectedText: function () {
    var t = '';

    if (window.getSelection) {
      t = window.getSelection();
    } else if (document.getSelection) {
      t = document.getSelection();
    } else if (document.selection) {
      t = document.selection.createRange().text;
    }

    return t;
  },


  /* Does the actual diffing */
  doDiff: function (a, b) {
    var d, op, text,
        textDiff = "",
        removed = "",
        diff = this.differencer.diff_main(a, b);

    this.differencer.diff_cleanupSemantic(diff);

    $.each(diff, function (k, v) {
      op = v[0];
      text = v[1];

      if (op === 0) {
          if (removed) {
            textDiff += '<span class="diff-delete">' + PTL.utils.fancyEscape(removed) + '</span>'
            removed = "";
          }
          textDiff += PTL.utils.fancyEscape(text);
      } else if (op === 1) {
        if (removed) {
          // This is part of a substitution, not a plain insertion. We
          // will format this differently.
          textDiff += '<span class="diff-replace">' + PTL.utils.fancyEscape(text) + '</span>';
          removed = "";
        } else {
          textDiff += '<span class="diff-insert">' + PTL.utils.fancyEscape(text) + '</span>';
        }
      } else if (op === -1) {
        removed = text;
      }
    });

    if (removed) {
      textDiff += '<span class="diff-delete">' + PTL.utils.fancyEscape(removed) + '</span>';
    }

    return textDiff;
  },


  /*
   * Fuzzying / unfuzzying functions
   */

  /* Sets the current unit's styling as fuzzy */
  doFuzzyArea: function () {
    $("tr.edit-row").addClass("fuzzy-unit");
  },


  /* Unsets the current unit's styling as fuzzy */
  undoFuzzyArea: function () {
    $("tr.edit-row").removeClass("fuzzy-unit");
  },


  /* Checks the current unit's fuzzy checkbox */
  doFuzzyBox: function () {
    $("input.fuzzycheck").attr("checked", "checked");
  },


  /* Unchecks the current unit's fuzzy checkbox */
  undoFuzzyBox: function () {
    $("input.fuzzycheck").removeAttr("checked");
  },


  /* Sets the current unit status as fuzzy (both styling and checkbox) */
  goFuzzy: function () {
    if (!this.isFuzzy()) {
      this.keepState = true;
      this.doFuzzyArea();
      this.doFuzzyBox();
    }
  },


  /* Unsets the current unit status as fuzzy (both styling and checkbox) */
  ungoFuzzy: function () {
    if (this.isFuzzy()) {
      this.keepState = true;
      this.undoFuzzyArea();
      this.undoFuzzyBox();
    }
  },


  /* Returns whether the current unit is fuzzy or not */
  isFuzzy: function () {
    return $("input.fuzzycheck").attr("checked");
  },


  /*
   * Suggest / submit mode functions
   */

  /* Changes the editor into suggest mode */
  doSuggestMode: function () {
    $("table.translate-table").addClass("suggest-mode");
  },


  /* Changes the editor into submit mode */
  undoSuggestMode: function () {
    $("table.translate-table").removeClass("suggest-mode");
  },


  /* Returns true if the editor is in suggest mode */
  isSuggestMode: function () {
    return $("table.translate-table").hasClass("suggest-mode");
  },


  /* Toggles suggest/submit modes */
  toggleSuggestMode: function () {
    if (this.isSuggestMode()) {
      this.undoSuggestMode();
    } else {
      this.doSuggestMode();
    }
  },

  updateExportLink: function () {
    var unit = this.units.getCurrent(),
        store = unit.get('store'),
        urlStr = [
          '', store.get('target_lang'), store.get('project_code'),
          'export-view', this.resourcePath
        ].join('/'),
        urlStr = [urlStr, $.param(this.getReqData())].join('?'),
        exportLink = [
          '<a href="', l(urlStr), '">', gettext('Export View'), '</a>'
        ].join('');

    $("#js-editor-export").html(exportLink);
  },

  /*
   * Indicators, messages, error handling
   */

  showActivity: function (force) {
    this.hideMsg();
    $("#js-editor-act").spin().fadeIn(300);
  },

  hideActivity: function () {
    $("#js-editor-act").spin(false).fadeOut(300);
  },

  /* Displays an informative message */
  displayMsg: function (msg) {
    this.hideActivity();
    $("#js-editor-msg").show().find("span").html(msg).fadeIn(300);
  },

  hideMsg: function (msg) {
    if ($("#js-editor-msg").is(":visible")) {
      $("#js-editor-msg").fadeOut(300);
    }
  },

  /* Displays error messages on top of the toolbar */
  displayError: function (msg) {
    if (msg) {
      this.hideActivity();
      $("#js-editor-error span").text(msg).parent().parent().stop(true, true)
                                .fadeIn(300).delay(2000).fadeOut(3500);
      }
  },


  /* Handles XHR errors */
  error: function (xhr, s) {
    var msg = "";

    if (s == "abort") {
        return;
    }

    if (xhr.status == 0) {
      msg = gettext("Error while connecting to the server");
    } else if (xhr.status == 500) {
      msg = gettext("Server error");
    } else if (s == "timeout") {
      msg = gettext("The server seems down. Try again later.");
    } else {
      // Since we use jquery-jsonp, we must differentiate between
      // the passed arguments
      if (xhr.hasOwnProperty('responseText')) {
        msg = $.parseJSON(xhr.responseText).msg;
      } else {
        msg = gettext("Unknown error");
      }
    }

    PTL.editor.displayError(msg);
  },


  /*
   * Misc functions
   */

  /* Gets common request data */
  getReqData: function () {
    var reqData = {};

    switch (this.filter) {

      case "checks":
        reqData.filter = this.filter;
        if (this.checks.length) {
          reqData.checks = this.checks.join(",");
        }
        break;

      case "search":
        reqData.search = this.searchText;
        reqData.sfields = this.searchFields;
        reqData.soptions = this.searchOptions;
        break;

      case "all":
        break;

      default:
        reqData.filter = this.filter;
        break;
    }

    if (this.user) {
      reqData.user = this.user;
    }

    if (this.goal) {
      reqData.goal = this.goal;
    }

    return reqData;
  },


  /*
   * Unit navigation, display, submission
   */

  /* Gets the view units that refer to the current page */
  getViewUnits: function (opts) {
    var extraData, reqData,
        defaults = {async: false, page: this.pager.current,
                    pager: false, withUid: 0},
        viewUrl = l('/xhr/units/');
    // Merge passed arguments with defaults
    opts = $.extend({}, defaults, opts);

    extraData = {
      page: opts.page,
      path: this.settings.pootlePath
    };
    if (opts.pager) {
      extraData.pager = opts.pager;
    }
    if (opts.withUid > 0) {
      extraData.uid = opts.withUid;
      // We don't know the page number beforehand —
      // delete the parameter as it's useless
      delete extraData.page
    }
    reqData = $.extend(extraData, this.getReqData());

    $.ajax({
      url: viewUrl,
      data: reqData,
      dataType: 'json',
      async: opts.async,
      success: function (data) {
        // Receive pager in case we have asked for it
        if (opts.pager && data.pager) {
          // FIXME: can we get rid of this, please?
          PTL.editor.hasResults = true;

          // Clear old data and add new results
          PTL.editor.pagesGot = {};
          PTL.editor.units.reset();
          PTL.editor.pager = data.pager;
        }

        // Store view units in the client
        if (data.unit_groups.length) {
          // Determine in which page we want to save units, as we may not
          // have specified it in the GET parameters — in that case, the
          // page number is specified within the response pager
          if (data.pager) {
            var page = data.pager.current;
          } else {
            var page = opts.page;
          }

          PTL.editor.pagesGot[page] = [];

          // Calculate where to insert the new set of units
          var pages = $.map(PTL.editor.pagesGot, function (value, key) {
                return parseInt(key, 10);
              }).sort(PTL.utils.numberCmp),
              pageIndex = pages.indexOf(page),
              at = PTL.editor.pager.perPage * pageIndex;

          // FIXME: can we avoid this?
          var urlStr = [
            PTL.editor.settings.ctxPath, 'translate/',
            PTL.editor.settings.resourcePath, '#unit=',
          ].join('');

          var i, j, unit, unitGroup;
          for (i=0; i<data.unit_groups.length; i++) {
            unitGroup = data.unit_groups[i];
            $.each(unitGroup, function (pootlePath, group) {
              var storeData = $.extend({pootlePath: pootlePath}, group.meta),
                  units = _.map(group.units, function (unit) {
                    return $.extend(unit, {store: storeData});
                  });
              PTL.editor.units.set(units, {at: at, remove: false});
              at += group.units.length;

              // FIXME: can we avoid this?
              for (j=0; j<group.units.length; j++) {
                unit = PTL.editor.units.get(group.units[j].id);
                unit.set('url', l(urlStr + unit.id));

                PTL.editor.pagesGot[page].push(unit.id);
              }
            });
          }

          if (opts.withUid) {
            PTL.editor.units.setCurrent(opts.withUid);
          } else if (data.pager) {
            var firstInPage = PTL.editor.pagesGot[data.pager.current][0];
            PTL.editor.units.setCurrent(firstInPage);
          }

          PTL.editor.hasResults = true;
        } else {
          PTL.editor.hasResults = false;
          $("table.translate-table").trigger("noResults");
        }
      },
      error: PTL.editor.error
    });
  },


  /* Builds a single row */
  buildRow: function (unit, cls) {
    return [
      '<tr id="row', unit.id, '" class="view-row ', cls ,'">',
        this.tmpl.vUnit({unit: unit.toJSON()}),
      '</tr>'
    ].join('');
  },

  /* Builds the editor rows */
  buildRows: function () {
    var unitGroups = this.getUnitGroups(),
        groupSize = _.size(unitGroups),
        currentUnit = this.units.getCurrent(),
        cls = "even",
        even = true,
        rows = [],
        i, unit;

    _.each(unitGroups, function (unitGroup) {
      // Don't display a delimiter row if all units have the same origin
      if (groupSize !== 1) {
        rows.push('<tr class="delimiter-row"><td colspan="2"></td></tr>');
      }

      for (i=0; i<unitGroup.length; i++) {
        unit = unitGroup[i];

        if (unit.id === currentUnit.id) {
          rows.push(this.getEditUnit());
        } else {
          rows.push(this.buildRow(unit, cls));
        }

        cls = even ? "odd" : "even";
        even = !even;
      }
    }, this);

    return rows.join('');
  },


  /* Builds context rows for units passed as 'units' */
  buildCtxRows: function (units, extraCls) {
    var i, unit,
        currentUnit = this.units.getCurrent(),
        cls = "even",
        even = true,
        rows = "",
        urlStr = [
          PTL.editor.settings.ctxPath, 'translate/',
          PTL.editor.settings.resourcePath, '#unit=',
        ].join('');

    for (i=0; i<units.length; i++) {
      // FIXME: Please let's use proper models for context units
      unit = units[i];
      unit['url'] = l(urlStr + unit.id);
      unit = $.extend({}, currentUnit.toJSON(), unit);

      rows += '<tr id="ctx' + unit.id + '" class="ctx-row ' + extraCls +
              ' ' + cls + '">';
      rows += this.tmpl.vUnit({unit: unit});
      rows += '</tr>';

      cls = even ? "odd" : "even";
      even = !even;
    }

    return rows;
  },


  /* Returns the unit groups for the current editor state */
  getUnitGroups: function () {
    var limit = parseInt(((this.pager.perPage - 1) / 2), 10),
        unitCount = this.units.length,
        currentUnit = this.units.getCurrent(),
        curIndex = this.units.indexOf(currentUnit),
        begin = curIndex - limit,
        end = curIndex + 1 + limit;

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

    return _.groupBy(this.units.slice(begin, end), function (unit) {
      return unit.get('store').get('pootlePath');
    }, this);
  },


  /* Sets the edit view for the current active unit */
  displayEditUnit: function () {
    if (PTL.editor.hasResults) {
      // Fetch pages asynchronously — we already have the needed pages
      // so this will return units whenever it can
      this.fetchPages();

      // Hide any visible message
      this.hideMsg();

      this.reDraw(this.buildRows());

      this.updateNavButtons();
    }
  },


  /* reDraws the translate table rows */
  reDraw: function (newTbody) {
    var tTable = $("table.translate-table"),
        where = $("tbody", tTable),
        oldRows = $("tr", where);

    oldRows.remove();

    // This fixes the issue with tipsy popups staying on the screen
    // if their owner elements have been removed
    $('.tipsy').remove(); // kill all open tipsy popups

    if (newTbody !== false) {
      where.append(newTbody);

      // We are ready, call the ready handlers
      $(tTable).trigger("editor_ready");
    }
  },


  /* Updates a button in `selector` to the `disable` state */
  updateNavButton: function (selector, disable) {
    var $el = $(selector);

    // Avoid unnecessary actions
    if ($el.is(':disabled') && disable || $el.is(':enabled') && !disable) {
      return;
    }

    if (disable) {
      $el.data('title', $el.attr('title'));
      $el.removeAttr('title');
    } else {
      $el.attr('title', $el.data('title'));
    }
    $el.prop('disabled', disable);
  },


  /* Updates previous/next navigation button states */
  updateNavButtons: function () {
    this.updateNavButton('#js-nav-prev', !this.units.hasPrev());
    this.updateNavButton('#js-nav-next', !this.units.hasNext());
  },


  /* Fetches more view unit pages in case they're needed */
  fetchPages: function (opts) {
    var defaults = {
          async: true,
          page: this.pager.current
        };

    opts = $.extend({}, defaults, opts);

    var current = opts.page,
        candidates = [current, current + 1, current - 1],
        pages = [],
        i;

    // We will only fetch valid pages and pages that haven't
    // already been fetched
    for (i=0; i<candidates.length; i++) {
      if (candidates[i] <= this.pager.numPages &&
          candidates[i] > 0 &&
          !(candidates[i] in this.pagesGot)) {
        pages.push(candidates[i]);
      }
    }

    // Do the actual fetching
    for (i=0; i<pages.length; i++) {
      this.getViewUnits({async: opts.async, page: pages[i]});
    }
  },

  /* Updates the pager */
  updatePager: function () {
    var pager = this.pager;

    $("#items-count").text(pager.count);

    var currentUnit = PTL.editor.units.getCurrent();
    if (currentUnit !== undefined) {
      // Calculate the global index number for the current unit.
      // Note that we can't just use `indexOf(currentUnit)` in the
      // collection because we don't load the entire collection at once
      var uId = currentUnit.id,
          uIndexInPage = PTL.editor.pagesGot[pager.current].indexOf(uId) + 1,
          uIndex = (pager.current - 1) * pager.perPage + uIndexInPage;
      $("#item-number").val(uIndex);
    }

  },

  /* Creates a pager based on the current client data and the given uid */
  createPager: function (uid) {
    var newPager = this.pager;
    // In case the given uid is not within the current page,
    // calculate in which page it is
    if ($.inArray(uid, this.pagesGot[this.pager.current]) == -1) {
      var newPageNumber,
          i = this.pager.current,
          j = this.pager.current + 1,
          found = false;
      // Search uid within the pages the client knows of
      while (!found && (i > 0 || j <= this.pager.numPages)) {
        if (i > 0 && $.inArray(uid, this.pagesGot[i]) != -1) {
          newPageNumber = i;
          found = true;
        } else if ($.inArray(uid, this.pagesGot[j]) != -1) {
          newPageNumber = j;
          found = true;
        }

        i--;
        j++;
      }

      if (found) {
        newPager.current = newPageNumber;
      }
    }

    return newPager;
  },

  /* Loads the edit unit for the current active unit */
  getEditUnit: function () {
    var editUnit, editCtxRowBefore, editCtxRowAfter, editCtxWidgets, hasData,
        eClass = "edit-row",
        currentUnit = this.units.getCurrent(),
        uid = currentUnit.id,
        editUrl = l(['/xhr/units/', uid, '/edit/'].join('')),
        reqData = this.getReqData(),
        widget = '',
        ctx = {before: [], after: []};

    $.ajax({
      url: editUrl,
      async: false,
      data: reqData,
      dataType: 'json',
      success: function (data) {
        widget = data['editor'];
        // Update pager in case it's needed
        PTL.editor.pager = PTL.editor.createPager(uid);
        PTL.editor.updatePager();

        if (data.ctx) {
          // Initialize context gap to the maximum context rows available
          PTL.editor.ctxGap = Math.max(data.ctx.before.length,
                                       data.ctx.after.length);
          ctx.before = data.ctx.before;
          ctx.after = data.ctx.after;
        }
      },
      error: PTL.editor.error
    });

    eClass += currentUnit.get('isfuzzy') ? " fuzzy-unit" : "";

    hasData = ctx.before.length || ctx.after.length;
    editCtxWidgets = this.editCtxUI({hasData: hasData});
    editCtxRowBefore = editCtxWidgets[0];
    editCtxRowAfter = editCtxWidgets[1];

    editUnit = (PTL.editor.filter !== 'all' ?
              editCtxRowBefore + this.buildCtxRows(ctx.before, "before") : '') +
             '<tr id="row' + uid + '" class="' + eClass + '">' +
             widget + '</tr>' +
             (PTL.editor.filter !== 'all' ?
              this.buildCtxRows(ctx.after, "after") + editCtxRowAfter : '');

    return editUnit;
  },

  /* Pushes translation submissions and moves to the next unit */
  submit: function (e) {
    e.preventDefault();

    var reqData, submitUrl, translations,
        unit = PTL.editor.units.getCurrent(),
        form = $("#captcha").ifExists() || $("#translate");

    submitUrl = l(['/xhr/units/', unit.id].join(''));

    // Serialize data to be sent and get required attributes for the request
    reqData = form.serializeObject();
    $.extend(reqData, PTL.editor.getReqData());

    $.ajax({
      url: submitUrl,
      type: 'POST',
      data: reqData,
      dataType: 'json',
      success: function (data) {
        if (data.captcha) {
          $.magnificPopup.open({
            items: {
              src: data.captcha,
              type: 'inline'
            },
            focus: '#id_captcha_answer'
          });
        } else {
          // FIXME: handle this via events
          translations = $("textarea[id^=id_target_f_]").map(function (i, el) {
            return $(el).val();
          }).get();
          unit.setTranslation(translations);
          unit.set('isfuzzy', PTL.editor.isFuzzy());

          PTL.editor.gotoNext();
        }
      },
      error: PTL.editor.error
    });
  },

  /* Pushes translation suggestions and moves to the next unit */
  suggest: function (e) {
    e.preventDefault();

    var reqData, suggestUrl,
        uid = PTL.editor.units.getCurrent().id,
        form = $("#captcha").ifExists() || $("#translate");

    suggestUrl = l(['/xhr/units/', uid, '/suggestions/'].join(''));

    // Serialize data to be sent and get required attributes for the request
    reqData = form.serializeObject();
    $.extend(reqData, PTL.editor.getReqData());

    $.ajax({
      url: suggestUrl,
      type: 'POST',
      data: reqData,
      dataType: 'json',
      success: function (data) {
        if (data.captcha) {
          $.magnificPopup.open({
            items: {
              src: data.captcha,
              type: 'inline'
            },
            focus: '#id_captcha_answer'
          });
        } else {
          PTL.editor.gotoNext();
        }
      },
      error: PTL.editor.error
    });
  },


  /* Loads the next unit */
  gotoNext: function () {
    // Buttons might be disabled so we need to fake an event
    PTL.editor.gotoPrevNext($.Event('click', {target: '#js-nav-next'}));
  },


  /* Loads the editor with the next unit */
  gotoPrevNext: function (e) {
    e.preventDefault();
    var prevNextMap = {'js-nav-prev': 'prev',
                       'js-nav-next': 'next'},
        elementId = e.target.id || $(e.target)[0].id,
        newUnit = PTL.editor.units[prevNextMap[elementId]]();

    // Try loading the prev/next unit
    if (newUnit) {
      var newHash = PTL.utils.updateHashPart("unit", newUnit.id);
      $.history.load(newHash);
    } else {
      if (elementId === 'js-nav-prev') {
        PTL.editor.displayMsg(gettext("You reached the beginning of the list"));
      } else {
        PTL.editor.displayMsg([
          gettext("You reached the end of the list."),
          '<br /><a href="', l(PTL.editor.settings.pootlePath), '">',
          gettext('Return to the overview page.'), '</a>'
        ].join(""));
      }
    }
  },


  /* Loads the editor with a specific unit */
  gotoUnit: function (e) {
    e.preventDefault();

    // Ctrl + click / Alt + click / Cmd + click / Middle click opens a new tab
    if (e.ctrlKey || e.altKey || e.metaKey || e.which === 2) {
      var $el = e.target.nodeName !== 'TD' ?
                  $(e.target).parents('td') :
                  $(e.target);
      window.open($el.data('target'), '_blank');
      return;
    }

    // Don't load anything if we're just selecting text
    if (PTL.editor.getSelectedText() != "") {
      return;
    }

    // Get clicked unit's uid from the row's id information and
    // try to load it
    var m = this.id.match(/(row|ctx)([0-9]+)/);
    if (m) {
      var newHash,
          type = m[1],
          uid = parseInt(m[2], 10);
      if (type === 'row') {
        newHash = PTL.utils.updateHashPart("unit", uid);
      } else {
        newHash = ['unit=', encodeURIComponent(uid)].join('');
      }
      $.history.load(newHash);
    }
  },

  /* Loads the editor on a index */
  // FIXME: we probably want to retrieve sorted list of all the UIDs
  // affecting the current query, so we wouldn't need to do ugly things
  // to figure out the mapping between indexes and unit IDs
  gotoIndex: function (index) {
    if (index && !isNaN(index) && index > 0 &&
        index <= PTL.editor.pager.count) {
      var preceding = index - 1,
          page = parseInt(preceding / PTL.editor.pager.perPage + 1, 10) || 1,
          uIndexInPage = preceding % PTL.editor.pager.perPage,
          uId;

      if (!(page in PTL.editor.pagesGot)) {
        PTL.editor.fetchPages({async: false, page: page});
      }

      uId = PTL.editor.pagesGot[page][uIndexInPage];

      var newHash = PTL.utils.updateHashPart("unit", uId);
      $.history.load(newHash);
    }
  },

  /*
   * Units filtering
   */

  /* Gets the failing check options for the current query */
  getCheckOptions: function () {
    var checksUrl = l('/xhr/checks/'),
        reqData = {
          path: this.settings.pootlePath,
          goal: this.goal
        },
        opts;

    $.ajax({
      url: checksUrl,
      async: false,
      data: reqData,
      dataType: 'json',
      success: function (data) {
        opts = data;
      },
      error: PTL.editor.error
    });

    return opts;
  },

  /* Loads units based on checks filtering */
  filterChecks: function () {
    if (PTL.editor.preventNavigation) {
      return;
    }
    var filterBy = $("option:selected", this).val();

    if (filterBy != "none") {
      var newHash = "filter=checks&checks=" + encodeURIComponent(filterBy);
      if (PTL.editor.goal) {
        newHash += '&goal=' + PTL.editor.goal;
      }
      $.history.load(newHash);
    }
  },

  /* Loads units based on filtering */
  filterStatus: function () {
    // this function can be executed in different contexts,
    // so using the full selector here
    var $selected = $("#filter-status option:selected"),
        filterBy = $selected.val(),
        isUserFilter = $selected.data('user');

    // Filtering by failing checks
    if (filterBy == "checks") {
      // Get actual failing checks
      var optGroups = PTL.editor.getCheckOptions();

      // If there are any failing checks, add them in a dropdown
      if (optGroups.length) {
        var dropdown = [
        '<div id="filter-checks">',
          '<select id="js-select2-filter-checks" ',
          'class="select2-filter-checks" name="filter-checks">',
          '<option selected="selected" value="none">------</option>'
        ]

        $.each(optGroups, function () {
          dropdown.push([
            '<optgroup label="', this.display_name, '">'
          ].join(''));
          $.each(this.checks, function () {
            dropdown.push([
              '<option value="', this.name, '">', this.display_name,
              ' (', this.count, ')</option>'
            ].join(''));
          });
          dropdown.push('</optgroup>');
        });

        dropdown.push('</select></div>');

        $("#filter-status").first().after(dropdown.join(''));
        $("#js-select2-filter-checks").select2({
          width: "resolve"
        });
      } else { // No results
        PTL.editor.displayMsg(gettext("No results."));
        $('#filter-status select').select2('val', PTL.editor.filter);
      }
    } else { // Normal filtering options (untranslated, fuzzy...)
      $("#filter-checks").remove();
      if (!PTL.editor.preventNavigation) {
        var newHash = "filter=" + filterBy;
        if (PTL.editor.user && isUserFilter) {
          newHash += '&user=' + PTL.editor.user;
        } else {
          PTL.editor.user = null;
          $(".js-user-filter").remove();
        }
        if (PTL.editor.goal) {
          newHash += '&goal=' + PTL.editor.goal;
        }
        $.history.load(newHash);
      }
    }
  },

  /* Generates the edit context rows' UI */
  editCtxUI: function (opts) {
    var defaults = {hasData: false, replace: false};
    opts = $.extend({}, defaults, opts);

    editCtxRowBefore = PTL.editor.tmpl.editCtx({hasData: opts.hasData,
                                                extraCls: 'before'});
    editCtxRowAfter = PTL.editor.tmpl.editCtx({hasData: opts.hasData,
                                               extraCls: 'after'});

    if (opts.replace) {
      $("tr.edit-ctx.before").replaceWith(editCtxRowBefore);
      $("tr.edit-ctx.after").replaceWith(editCtxRowAfter);
    }

    return [editCtxRowBefore, editCtxRowAfter];
  },

  /* Gets more context units */
  moreContext: function (initial) {
    var ctxUrl = l(['/xhr/units/', PTL.editor.units.getCurrent().id, '/context/'].join('')),
        reqData = {gap: PTL.editor.ctxGap};

    reqData.qty = initial ? PTL.editor.ctxQty : PTL.editor.ctxStep;

    // Don't waste a request if nothing is expected initially
    if (initial && reqData.qty === 0) {
      return;
    }

    $.ajax({
      url: ctxUrl,
      async: false,
      dataType: 'json',
      data: reqData,
      success: function (data) {
        if (data.ctx.before.length || data.ctx.after.length) {
          // As we now have got more context rows, increase its gap
          if (initial) {
            PTL.editor.ctxGap = Math.max(data.ctx.before.length,
                                         data.ctx.after.length);
          } else {
            PTL.editor.ctxGap += Math.max(data.ctx.before.length,
                                          data.ctx.after.length);
          }
          $.cookie('ctxQty', PTL.editor.ctxGap, {path: '/'});

          // Create context rows HTML
          var before = PTL.editor.buildCtxRows(data.ctx.before, "before"),
              after = PTL.editor.buildCtxRows(data.ctx.after, "after");

          // Append context rows to their respective places
          var editCtxRows = $("tr.edit-ctx");
          editCtxRows.first().after(before);
          editCtxRows.last().before(after);
        }
      },
      error: PTL.editor.error
    });
  },

  /* Shrinks context lines */
  lessContext: function () {

    var before = $(".ctx-row.before"),
        after = $(".ctx-row.after");

    // Make sure there are context rows before decreasing the gap and
    // removing any context rows
    if (before.length || after.length) {
      if (before.length === PTL.editor.ctxGap) {
        before.slice(0, PTL.editor.ctxStep).remove();
      }

      if (after.length === PTL.editor.ctxGap) {
        after.slice(-PTL.editor.ctxStep).remove();
      }

      PTL.editor.ctxGap -= PTL.editor.ctxStep;

      if (PTL.editor.ctxGap >= 0) {
        if (PTL.editor.ctxGap == 0) {
          PTL.editor.editCtxUI({hasData: false, replace: true});
          $.cookie('ctxShow', false, {path: '/'});
        }

        $.cookie('ctxQty', PTL.editor.ctxGap, {path: '/'});
      }
    }
  },

  /* Shows context rows */
  showContext: function () {

    var editCtxRowBefore, editCtxRowAfter,
        before = $(".ctx-row.before"),
        after = $(".ctx-row.after");

    if (before.length || after.length) {
      before.show();
      after.show();
    } else {
      PTL.editor.moreContext(true);
    }

    PTL.editor.editCtxUI({hasData: true, replace: true});
    $.cookie('ctxShow', true, {path: '/'});
  },

  /* Hides context rows */
  hideContext: function () {

    var editCtxRowBefore, editCtxRowAfter,
        before = $(".ctx-row.before"),
        after = $(".ctx-row.after");

    before.hide();
    after.hide();

    PTL.editor.editCtxUI({hasData: false, replace: true});
    $.cookie('ctxShow', false, {path: '/'});
  },


  /* Loads the search view */
  search: function (e) {
    e.preventDefault();

    var newHash,
        text = $("#id_search").val();

    if (text) {
      var remember = true,
          queryString = PTL.search.buildSearchQuery(text, remember);
      newHash = "search=" + queryString;
    } else {
      newHash = PTL.utils.updateHashPart("filter", "all", ["search", "sfields","soptions"]);
    }
    if (PTL.editor.goal) {
      newHash += '&goal=' + PTL.editor.goal;
    }
    $.history.load(newHash);
  },


  /*
   * Comments
   */
  comment: function (e) {
    e.preventDefault();

    var url = $(this).attr('action'),
        reqData = $(this).serializeObject();

    $.ajax({
      url: url,
      type: 'POST',
      data: reqData,
      success: function (data) {
        $("#editor-comment").fadeOut(200);

        if ($("#translator-comment").length) {
          $(data.comment).hide().prependTo("#translator-comment").delay(200)
                         .animate({height: 'show'}, 1000, 'easeOutQuad');
        } else {
          var commentHtml = '<div id="translator-comment">' + data.comment
                          + '</div>';
          $(commentHtml).prependTo("#extras-container").delay(200)
                        .hide().animate({height: 'show'}, 1000, 'easeOutQuad');
        }

        PTL.common.updateRelativeDates();
      },
      error: PTL.editor.error
    });

    return false;
  },


  /*
   * Unit timeline
   */

  /* Get the timeline data */
  showTimeline: function (e) {
    e.preventDefault();

    // The results might already be there from earlier:
    if ($("#timeline-results").length) {
      $("#js-hide-timeline").show();
      $("#timeline-results").slideDown(1000, 'easeOutQuad');
      $("#js-show-timeline").hide();
      return;
    }

    var uid = PTL.editor.units.getCurrent().id,
        node = $("#extras-container"),
        timelineUrl = l(['/xhr/units/', uid, '/timeline/'].join(''));

    // Always abort previous requests so we only get results for the
    // current unit
    if (PTL.editor.timelineReq != null) {
      PTL.editor.timelineReq.abort();
    }

    PTL.editor.timelineReq = $.ajax({
      url: timelineUrl,
      dataType: 'json',
      success: function (data) {
        var uid = data.uid;

        if (data.timeline && uid === PTL.editor.units.getCurrent().id) {
          if ($("#translator-comment").length) {
            $(data.timeline).hide().insertAfter("#translator-comment")
                            .slideDown(1000, 'easeOutQuad');
          } else {
            $(data.timeline).hide().prependTo("#extras-container")
                            .slideDown(1000, 'easeOutQuad');
          }

          PTL.common.updateRelativeDates();

          $('.timeline-field-body').filter(':not([dir])').bidi();
          $("#js-show-timeline").hide();
          $("#js-hide-timeline").show();
        }
      },
      beforeSend: function () {
        node.spin();
      },
      complete: function () {
        node.spin(false);
      },
      error: PTL.editor.error
    });
  },

 /* Hide the timeline panel */
  hideTimeline: function (e) {
    $("#js-hide-timeline").hide();
    $("#timeline-results").slideUp(1000, 'easeOutQuad');
    $("#js-show-timeline").show();
  },


  /*
   * User and TM suggestions
   */

  /* Filters TM results and does some processing (add diffs, extra texts...) */
  filterTMResults: function (results) {
    // FIXME: this just retrieves the first four results
    // we could limit based on a threshold too.
    var source = $("[id^=id_source_f_]").first().val(),
        filtered = [],
        quality;

    for (var i=0; i<results.length && i<3; i++) {
      results[i].source = this.doDiff(source, results[i].source);
      results[i].target = PTL.utils.fancyHl(results[i].target);
      quality = Math.round(results[i].quality);
      // Translators: This is the quality match percentage of a TM result.
      // '%s' will be replaced by a number, and you should keep the extra
      // '%' symbol to denote a percentage is being used.
      results[i].qTitle = interpolate(gettext('%s% match'), [quality]);
      filtered.push(results[i]);
    }

    return filtered;
  },


  /* Gets TM suggestions from amaGama */
  getTMUnits: function () {
    var unit = this.units.getCurrent(),
        store = unit.get('store'),
        src = store.get('source_lang'),
        tgt = store.get('target_lang'),
        sText = unit.get('source')[0],
        pStyle = store.get('project_style'),
        tmUrl = this.settings.tmUrl + src + "/" + tgt +
          "/unit/?source=" + encodeURIComponent(sText) + "&jsoncallback=?";

    if (!sText.length) {
        // No use in looking up an empty string
        return;
    }

    if (pStyle.length && pStyle != "standard") {
        tmUrl += '&style=' + pStyle;
    }

    // Always abort previous requests so we only get results for the
    // current unit
    if (this.tmReq != null) {
      this.tmReq.abort();
    }

    this.tmReq = $.jsonp({
      url: tmUrl,
      callback: '_jsonp' + PTL.editor.units.getCurrent().id,
      dataType: 'jsonp',
      cache: true,
      success: function (data) {
        var uid = this.callback.slice(6);

        if (uid == PTL.editor.units.getCurrent().id && data.length) {
          var filtered = PTL.editor.filterTMResults(data),
              name = gettext("Similar translations"),
              tm = PTL.editor.tmpl.tm({store: store.toJSON(),
                                       suggs: filtered,
                                       name: name});

          $(tm).hide().appendTo("#extras-container")
                      .slideDown(1000, 'easeOutQuad');
        }
      },
      error: PTL.editor.error
    });
  },


  /* Rejects a suggestion */
  rejectSuggestion: function (e) {
    e.stopPropagation(); //we don't want to trigger a click on the text below
    var suggId = $(this).data("sugg-id"),
        element = $("#suggestion-" + suggId);
        uid = $('.translate-container #id_id').val(),
        url = l(['/xhr/units/', uid,
                 '/suggestions/', suggId, '/reject/'].join(''));

    $.post(url, {'reject': 1},
      function (data) {
        element.fadeOut(200, function () {
          $(this).remove();

          // Go to the next unit if there are no more suggestions left
          if (!$("#suggestions div[id^=suggestion]").length) {
            PTL.editor.gotoNext();
          }
        });
      }, "json");
  },


  /* Accepts a suggestion */
  acceptSuggestion: function (e) {
    e.stopPropagation(); //we don't want to trigger a click on the text below
    var suggId = $(this).data("sugg-id"),
        element = $("#suggestion-" + suggId),
        unit = PTL.editor.units.getCurrent(),
        url = l(['/xhr/units/', unit.id,
                 '/suggestions/', suggId, '/accept/'].join('')),
        translations;

    $.post(url, {'accept': 1},
      function (data) {
        // Update target textareas
        $.each(data.newtargets, function (i, target) {
          $("#id_target_f_" + i).val(target).focus();
        });

        // Update remaining suggestion's diff
        $.each(data.newdiffs, function (suggId, sugg) {
          $.each(sugg, function (i, target) {
             $("#suggdiff-" + suggId + "-" + i).html(target);
          });
        });

        // FIXME: handle this via events
        translations = $("textarea[id^=id_target_f_]").map(function (i, el) {
          return $(el).val();
        }).get();
        unit.setTranslation(translations);
        unit.set('isfuzzy', false);

        element.fadeOut(200, function () {
          $(this).remove();

          // Go to the next unit if there are no more suggestions left
          if (!$("#suggestions div[id^=suggestion]").length) {
            PTL.editor.gotoNext();
          }
        });
      }, "json");
  },

  /* Clears the vote for a specific suggestion */
  clearVote: function (e) {
    e.stopPropagation(); //we don't want to trigger a click on the text below
    var element = $(this),
        voteId = element.data("vote-id"),
        url = l(['/xhr/votes/', voteId, '/clear/'].join(''));

    element.fadeTo(200, 0.01); //instead of fadeOut that will cause layout changes
    $.ajax({
      url: url,
      type: 'POST',
      data: {'clear': 1},
      dataType: 'json',
      success: function (data) {
        element.hide();
        element.siblings(".js-vote-up").fadeTo(200, 1);
      },
      error: function (xhr, s) {
        PTL.editor.error(xhr, s);
        //Let's wait a while before showing the voting widget again
        element.delay(3000).fadeTo(2000, 1);
      }
    });
  },

  /* Votes for a specific suggestion */
  voteUp: function (e) {
    e.stopPropagation();
    var element = $(this),
        suggId = element.siblings("[data-sugg-id]").data("sugg-id"),
        url = l(['/xhr/units/', PTL.editor.units.getCurrent().id,
                 '/suggestions/', suggId, '/votes/'].join(''));

    element.fadeTo(200, 0.01); //instead of fadeOut that will cause layout changes
    $.ajax({
      url: url,
      type: 'POST',
      data: {'up': 1},
      dataType: 'json',
      success: function (data) {
        element.siblings("[data-vote-id]").data("vote-id", data.voteid);
        element.hide();
        element.siblings(".js-vote-clear").fadeTo(200, 1);
      },
      error: function (xhr, s) {
        PTL.editor.error(xhr, s);
        //Let's wait a while before showing the voting widget again
        element.delay(3000).fadeTo(2000, 1);
      }
    });
  },

  /* Rejects a quality check marking it as false positive */
  rejectCheck: function () {
    var element = $(this).parent(),
        checkId = $(this).data("check-id"),
        uid = $('.translate-container #id_id').val(),
        url = l(['/xhr/units/', uid, '/checks/', checkId, '/reject/'].join(''));

    $.post(url, {'reject': 1},
      function (data) {
        if (element.siblings().size() == 0) {
          element = $('#translate-checks-block');
        }
        element.fadeOut(200, function () {
          $(this).remove();
          $('.tipsy').remove();
        });
      }, "json");
  },


  /*
   * Machine Translation
   */

  /* Checks whether the provided source is supported */
  isSupportedSource: function (pairs, source) {
    for (var i in pairs) {
      if (source == pairs[i].source) {
        return true;
      }
    }
    return false;
  },


  /* Checks whether the provided target is supported */
  isSupportedTarget: function (pairs, target) {
    for (var i in pairs) {
      if (target == pairs[i].target) {
        return true;
      }
    }
    return false;
  },


  /* Checks whether the provided source-target pair is supported */
  isSupportedPair: function (pairs, source, target) {
    for (var i in pairs) {
      if (source == pairs[i].source &&
          target == pairs[i].target) {
        return true;
      }
    }
    return false;
  },


  /* Adds a new MT service button in the editor toolbar */
  addMTButton: function (container, aClass, tooltip) {
      var btn = '<a class="translate-mt ' + aClass + '">';
      btn += '<i class="icon-' + aClass+ '" title="' + tooltip + '"><i/></a>';
      $(container).first().prepend(btn);
  },

  /* Goes through all source languages and adds a new MT service button
   * in the editor toolbar if the language is supported
   */
  addMTButtons: function (provider) {
    if (this.isSupportedTarget(provider.pairs, PTL.editor.settings.targetLang)) {
      var _this = this;
      var sources = $(".translate-toolbar");
      $(sources).each(function () {
        var source = _this.normalizeCode($(this).parent().parent().find('.translation-text').attr("lang"));

        var ok;
        if (provider.validatePairs) {
          ok = _this.isSupportedPair(provider.pairs, source, PTL.editor.settings.targetLang);
        } else {
          ok = _this.isSupportedSource(provider.pairs, source);
        }

        if (ok) {
          _this.addMTButton(this,
            provider.buttonClassName,
            provider.hint + ' (' + source.toUpperCase() + '&rarr;' + PTL.editor.settings.targetLang.toUpperCase() + ')');
        }
      });
    }
  },

  /* Normalizes language codes in order to use them in MT services */
  normalizeCode: function (locale) {
    if (locale) {
      var clean = locale.replace('_', '-')
      var atIndex = locale.indexOf('@');
      if (atIndex !== -1) {
        clean = clean.slice(0, atIndex);
      }
      return clean;
    }
    return locale;
  },

  collectArguments: function (s) {
    this.argSubs[this.argPos] = s;
    return "[" + (this.argPos++) + "]";
  },

  translate: function (linkObject, providerCallback) {
    var areas = $("[id^=id_target_f_]");
    var sources = $(linkObject).parent().parent().parent().find('.translation-text');
    var langFrom = PTL.editor.normalizeCode(sources.eq(0).attr("lang"));
    var langTo = PTL.editor.normalizeCode(areas.eq(0).attr("lang"));

    var htmlPat = /<[\/]?\w+.*?>/g;
    // The printf regex based on http://phpjs.org/functions/sprintf:522
    var cPrintfPat = /%%|%(\d+\$)?([-+\'#0 ]*)(\*\d+\$|\*|\d+)?(\.(\*\d+\$|\*|\d+))?([scboxXuidfegEG])/g;
    var csharpStrPat = /{\d+(,\d+)?(:[a-zA-Z ]+)?}/g;
    var percentNumberPat = /%\d+/g;
    var pos = 0;

    var _this = this;

    $(sources).each(function (j) {
      var sourceText = $(this).text();

      // Reset collected arguments array and counter
      _this.argSubs = new Array();
      _this.argPos = 0;

      // Walk through known patterns and replace them with [N] placeholders

      sourceText = sourceText.replace(htmlPat, function(s) { return _this.collectArguments(s) });
      sourceText = sourceText.replace(cPrintfPat, function(s) { return _this.collectArguments(s) });
      sourceText = sourceText.replace(csharpStrPat, function(s) { return _this.collectArguments(s) });
      sourceText = sourceText.replace(percentNumberPat, function(s) { return _this.collectArguments(s) });

      var result = providerCallback(sourceText, langFrom, langTo, function(translation, message) {
        if (translation === false) {
          PTL.editor.displayError(message);
          return;
        }

        // Fix whitespace which may have been added around [N] blocks
        for (var i = 0; i < _this.argSubs.length; i++) {
          if (sourceText.match(new RegExp("\\[" + i + "\\][^\\s]"))) {
            translation = translation.replace(new RegExp("\\[" + i + "\\]\\s+"), "[" + i + "]");
          }
          if (sourceText.match(new RegExp("[^\\s]\\[" + i + "\\]"))) {
            translation = translation.replace(new RegExp("\\s+\\[" + i + "\\]"), "[" + i + "]");
          }
        }

        // Replace temporary [N] placeholders back to their real values
        for (var i = 0; i < _this.argSubs.length; i++) {
          var value = _this.argSubs[i].replace(/\&/g, "&amp;").replace(/\</g, "&lt;").replace(/\>/g, "&gt;");
          translation = translation.replace("[" + i + "]", value);
        }

        areas.eq(j).val($('<div />').html(translation).text());
        areas.eq(j).focus();
      });
    });

    PTL.editor.goFuzzy();
    return false;
  },


  /*
   * Lookup
   */

  /* Adds a new Lookup button in the editor toolbar */
  addLookupButton: function (container, aClass, tooltip) {
    $(container).first().prepend(['<a class="translate-lookup iframe ',
      aClass, '"><i class="icon-', aClass, '" title="', tooltip,
      '"></i></a>'].join(''));
  },

  /* Goes through all source languages and adds a new lookup service button
   * in the editor toolbar if the language is supported
   */
  addLookupButtons: function (provider) {
    var _this = this;
    var sources = $(".translate-toolbar");
    $(sources).each(function () {
      var source = _this.normalizeCode($(this).parent().parent().find('.translation-text').attr("lang"));

    _this.addLookupButton(this,
      provider.buttonClassName,
      [provider.hint, ' (', source.toUpperCase(), ')'].join(''));
    });
  },

  lookup: function (linkObject, providerCallback) {
    var areas = $("[id^=id_target_f_]");
    var sources = $(linkObject).parent().parent().parent().find('.translation-text');
    var langFrom = PTL.editor.normalizeCode(sources.eq(0).attr("lang"));
    var langTo = PTL.editor.normalizeCode(areas.eq(0).attr("lang"));

    var lookupText = PTL.editor.getSelectedText().toString();
    if (!lookupText) {
      lookupText = sources.eq(0).text();
    }
    var url = providerCallback(lookupText, langFrom, langTo);
    $.magnificPopup.open({
      items: {
        src: url,
        type: 'iframe'
      },
    });
    linkObject.href = url;
    return false;
  }


  }; // PTL.editor

}(jQuery));
