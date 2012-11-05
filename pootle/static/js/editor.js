(function ($) {

  window.PTL = window.PTL || {};

  PTL.editor = {

  /* Initializes the editor */
  init: function (options) {

    /* Default settings */
    this.settings = {
      secure: false,
      mt: []
    };
    /* Merge given options with default settings */
    if (options) {
      $.extend(this.settings, options);
    }

    /* Initialize variables */
    this.units = {};
    this.store = $("#editor").data("pootle-path");
    this.directory = $("#editor").data("directory");
    this.currentPage = 1;
    this.currentNumPages = 0;
    this.pagesGot = {};
    this.filter = "all";
    this.checks = [];
    this.ctxGap = 0;
    this.ctxQty = parseInt($.cookie('ctxQty')) || 1;
    this.ctxStep= 1;
    this.keepState = false;
    this.preventNavigation = false;

    this.isLoading = true;
    this.showActivity();

    /* Currently active search fields */
    this.searchFields = [];

    /* Regular expressions */
    this.cpRE = /^(<[^>]+>|\[n\|t]|\W$^\n)*(\b|$)/gm;
    this.escapeRE = /<[^<]*?>|\r\n|[\r\n\t&<>]/gm;
    this.whitespaceRE = /^ +| +$|[\r\n\t] +| {2,}/gm;

    /* Timeline requests handler */
    this.timelineReq = null;

    /* TM requests handler */
    this.tmReq = null;

    /* Differencer */
    this.differencer = new diff_match_patch();

    /* Compile templates */
    this.tmpl = {vUnit: $.template($("#view_unit").html()),
                 tm: $.template($("#tm_suggestions").html()),
                 editCtx: $.template($("#editCtx").html())}

    /* Initialize search */
    // TODO: pass the environment option to the init
    PTL.search.init();

    /*
     * Bind event handlers
     */

    /* Fuzzy / unfuzzy */
    $(document).on("keyup blur", "textarea.translation", function () {
      if (!PTL.editor.keepState &&
          $(this).prop("defaultValue") != $(this).val()) {
        PTL.editor.ungoFuzzy();
      }
    });
    $(document).on("click", "input.fuzzycheck", function () {
      if (PTL.editor.isFuzzy()) {
        PTL.editor.doFuzzyArea();
      } else {
        PTL.editor.undoFuzzyArea();
      }
    });

    /* Suggest / submit */
    $(document).on("click", ".switch-suggest-mode a", function () {
      PTL.editor.toggleSuggestMode();
      return false;
    });

    /* Update focus when appropriate */
    $(document).on("focus", ".focusthis", function (e) {
      PTL.editor.focused = e.target;
    });

    /* Write TM results, special chars... into the currently focused element */
    $(document).on("click", ".js-editor-copytext", this.copyText);

    /* Copy original translation */
    $(document).on("click", ".js-copyoriginal", function () {
      var sources = $(".translation-text", $(this).parent().parent().parent());
      PTL.editor.copyOriginal(sources);
    });

    /* Copy suggestion */
    $(document).on("click", "div.suggestion", function () {
      // Don't copy if text has been selected
      if (PTL.editor.getSelectedText() != "") {
        return;
      }
      if ($("#id_target_f_0").attr("disabled")) {
        return;
      }
      var sources = $(".suggestion-translation", this);
      PTL.editor.copyOriginal(sources);
    });

    /* Editor navigation/submission */
    $(document).on("editor_ready", "table.translate-table", this.ready);
    $(document).on("noResults", "table.translate-table", this.noResults);
    $(document).on("click", "tr.view-row", this.gotoUnit);
    $(document).on("keypress", "#item-number", function (e) {
        // Perform action only when the 'Enter' key is pressed
        if (e.keyCode == 13) {
          PTL.editor.gotoPage(parseInt($("#item-number").val()));
        }
    });
    $(document).on("click", "input.submit", this.submit);
    $(document).on("click", "input.suggest", this.suggest);
    $(document).on("click", "input.previous, input.next", this.gotoPrevNext);
    $(document).on("click", ".js-suggestion-reject", this.rejectSuggestion);
    $(document).on("click", ".js-suggestion-accept", this.acceptSuggestion);
    $(document).on("click", ".js-vote-clear", this.clearVote);
    $(document).on("click", ".js-vote-up", this.voteUp);
    $(document).on("click", "#js-show-timeline", this.showTimeline);
    $(document).on("click", "#js-hide-timeline", this.hideTimeline);
    $(document).on("click", "#translate-checks-block .js-reject-check", this.rejectCheck);

    /* Filtering */
    $(document).on("change", "#filter-status select", this.filterStatus);
    $(document).on("change", "#filter-checks select", this.filterChecks);
    $(document).on("click", ".js-more-ctx", function () {
      PTL.editor.moreContext(false)
    });
    $(document).on("click", ".js-less-ctx", this.lessContext);
    $(document).on("click", ".js-show-ctx", this.showContext);
    $(document).on("click", ".js-hide-ctx", this.hideContext);

    /* Commenting */
    $(document).on("click", ".js-editor-comment", function (e) {
      e.preventDefault();
      $("#editor-comment").slideToggle("fast");
    });
    $(document).on("submit", "#comment-form", this.comment);

    /* Search */
    $(document).on("keypress", "#id_search", function (e) {
        if (e.keyCode == 13) {
          e.preventDefault();
          PTL.editor.search();
        }
    });

    /* Bind hotkeys */
    shortcut.add('ctrl+return', function () {
      if (PTL.editor.isSuggestMode()) {
        $("input.suggest").trigger("click");
      } else {
        $("input.submit").trigger("click");
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
      $("input.previous").trigger("click");
    });
    shortcut.add('ctrl+down', function () {
      $("input.next").trigger("click");
    });
    shortcut.add('ctrl+shift+home', function () {
      PTL.editor.gotoFirstPage();
    });
    shortcut.add('ctrl+shift+end', function () {
      PTL.editor.gotoLastPage();
    });
    shortcut.add('ctrl+shift+pageup', function () {
      PTL.editor.gotoPrevPage();
    });
    shortcut.add('ctrl+shift+pagedown', function () {
      PTL.editor.gotoNextPage();
    });
    shortcut.add('ctrl+shift+u', function () {
      $("#item-number").focus().select();
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
      var backend = this.name;
      var key = this.key;

      $.ajax({
        url: s('js/mt/' + backend + '.js'),
        async: false,
        dataType: 'script',
        success: function () {
          setTimeout(function () {
            PTL.editor.mt[backend].init(key);
          }, 0);
          $(document).on("mt_ready", "table.translate-table",
                         PTL.editor.mt[backend].ready);
        }
      });
    });

    /* Load lookup backends */
    $.each(this.settings.lookup, function () {
      var backend = this;

      $.ajax({
        url: s('js/lookup/' + backend + '.js'),
        async: false,
        dataType: 'script',
        success: function () {
          setTimeout(function () {
            PTL.editor.lookup[backend].init();
          }, 0);
          $(document).on("lookup_ready", "table.translate-table",
                         PTL.editor.lookup[backend].ready);
        }
      });
    });

    /* History support */
    setTimeout(function () {
      $.history.init(function (hash) {
        var params = PTL.utils.getParsedHash(hash);

        var withUid = false;
        var pageNumber = undefined;

        // Walk through known filtering criterias and apply them to the editor object

        if ('unit' in params) {
          var uid = parseInt(params['unit']);

          if (uid && !isNaN(uid)) {
            if (PTL.editor.activeUid != uid &&
                PTL.editor.units[uid] == undefined) {
              PTL.editor.activeUid = uid;
              withUid = true;
            } else {
              // if uid is already preloaded, just switch to it
              PTL.editor.activeUid = uid;
              PTL.editor.displayEditUnit(uid);
              return;
            }
          }
        } else if ('page' in params) {
          var p = parseInt(params['page']);

          if (p && !isNaN(p) && p > 0) {
            pageNumber = p;
          }
        }

        if ('filter' in params) {
          var a = params['filter'].split(',');

          // Set current state
          PTL.editor.filter = a.shift();
          PTL.editor.checks = (PTL.editor.filter == "checks") ? a : [];
        }

        if ('search' in params) {
          // Note that currently the search, if provided along with the other filters,
          // would override them
          PTL.editor.filter = "search";
          PTL.editor.searchText = params['search'];
          if ('sfields' in params) {
            PTL.editor.searchFields = params['sfields'].split(',');
          }
        }

        // Update the filter UI to match the current filter

        // disable navigation on UI toolbar events to prevent data reload
        PTL.editor.preventNavigation = true;

        $("#filter-status select [value='" + PTL.editor.filter + "']").attr("selected", "selected");
        if (PTL.editor.filter == "checks") {
          // if the checks selector is empty (i.e. the 'change' event was not fired
          // because the selection did not change), force the update to populate the selector
          if (!$("#filter-checks").length) {
            PTL.editor.filterStatus();
          }
          $("#filter-checks select [value='" + PTL.editor.checks[0] + "']").attr("selected", "selected");
        }

        if (PTL.editor.filter == "search") {
          $("#id_search").triggerHandler('focus');
          $("#id_search").val(PTL.editor.searchText);

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
        }
        // re-enable normal event handling
        PTL.editor.preventNavigation = false;

        // Load the units that match the given criterias
        PTL.editor.getViewUnits({pager: true, page: pageNumber,
                                 withUid: withUid});

        if (PTL.editor.hasResults) {
          // ensure all the data is preloaded before rendering the table
          // otherwise, when the page is reloaded, some pages will not yet be there
          PTL.editor.fetchPages(false);

          // now we can safely render the table
          PTL.editor.displayEditUnit(PTL.editor.activeUid);
        }

      }, {'unescape': true});
    }, 1); // not sure why we had a 1000ms timeout here

  },

  /* Stuff to be done when the editor is ready  */
  ready: function () {
    // Set textarea's initial height as well as the max-height
    var maxheight = $(window).height() * 0.3;
    $('textarea.expanding').TextAreaExpander('10', maxheight);

    // Focus on the first textarea, if any
    if ($(".focusthis").get(0)) {
      $(".focusthis").get(0).focus();
    }

    // Highlight stuff
    PTL.editor.hlSearch();
    //PTL.editor.hlTerms(); // Disabled for now — it's annoying!

    if (PTL.editor.settings.tmUrl != '') {
      // Start retrieving TM units from amaGama
      PTL.editor.getTMUnits();
    }

    // All is ready, let's call the ready functions of the MT backends
    $("table.translate-table").trigger("mt_ready");
    $("table.translate-table").trigger("lookup_ready");

    PTL.editor.isLoading = false;
    PTL.editor.hideActivity();
    PTL.editor.updatePermalink();

    // clear any pending 'Loading...' indicator timer
    // as ajaxStop() is not fired in IE properly
    // at initial page load (?!)
    clearTimeout(PTL.editor.delayedActivityTimer);
  },

  /* Things to do when no results are returned */
  noResults: function () {
    PTL.editor.displayError(gettext("No results."));
    PTL.editor.reDraw(false);
    PTL.editor.updatePermalink(false);
  },


  /*
   * Text utils
   */

  escapeUnsafeRegexSymbols: function (s) {
    var i, r = "\\.+*?[^]$(){}=!<>¦:";
    for (i = 0; i < r.length; i++) {
      s = s.replace(new RegExp("\\" + r.charAt(i),"g"), "\\" + r.charAt(i));
    }
    return s;
  },

  makeRegexForMultipleWords: function (s) {
    var i, w = s.split(' ');
    for (i = 0; i < w.length; i++) {
      w[i] = this.escapeUnsafeRegexSymbols(w[i]);
    }
    return '(' + w.join("|") + ')';
  },

  /* Highlights search results */
  hlSearch: function () {
    var hl = PTL.editor.filter == "search" ? PTL.editor.searchText : "",
        sel = [],
        selMap = {notes: "div.developer-comments",
                  locations: "div.translate-locations",
                  source: "td.translate-original, div.original div.translation-text",
                  target: "td.translate-translation"};

    // Build highlighting selector based on chosen search fields
    $.each(PTL.editor.searchFields, function (i, field) {
      sel.push("tr.edit-row " + selMap[field]);
      sel.push("tr.view-row " + selMap[field]);
    });

    $(sel.join(", ")).highlightRegex(new RegExp(PTL.editor.makeRegexForMultipleWords(hl), "i"));
  },

  /* Highlights matching terms in the source text */
  hlTerms: function () {
    var term;

    $(".tm-original").each(function () {
      term = $(this).text();
      $("div.original .translation-text").highlightRegex(new RegExp(PTL.editor.escapeUnsafeRegexSymbols(term), "g"));
    });
  },


  /* Copies text into the focused textarea */
  copyText: function (e) {
    var selector, text, element, start,
        action = $(this).data('action');

    // Determine which text we need
    selector = $(".tm-translation", this).ifExists() ||
               $(".suggestion-translation", this).ifExists() || $(this);
    text = selector.text();

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

  /* Cleans '\n' escape sequences and adds '\t' sequences */
  cleanEscape: function (s) {
    return s.replace(/\\t/g, "\t").replace(/\\n/g, "");
  },


  /* Fancy escapes to highlight parts of the text such as HTML tags */
  fancyEscape: function (text) {

    function replace(match) {
        var replaced,
            escapeHl= '<span class="highlight-escape">%s</span>',
            htmlHl = '<span class="highlight-html">&lt;%s&gt;</span>',
            submap = {
              '\r\n': escapeHl.replace(/%s/, '\\r\\n') + '<br/>\n',
              '\r': escapeHl.replace(/%s/, '\\r') + '<br/>\n',
              '\n': escapeHl.replace(/%s/, '\\n') + '<br/>\n',
              '\t': escapeHl.replace(/%s/, '\\t'),
              '&': '&amp;',
              '<': '&lt;',
              '>': '&gt;'
            };

        replaced = submap[match];

        if (replaced == undefined) {
          replaced = htmlHl.replace(/%s/, match.slice(1, match.length-1));
        }

        return replaced;
    }

    return text.replace(this.escapeRE, replace);
  },


  /* Highlight spaces to make them easily visible */
  fancySpaces: function (text) {

    function replace(match) {
        var spaceHl= '<span class="translation-space"> </span>';

        return Array(match.length + 1).join(spaceHl);
    }

    return text.replace(this.whitespaceRE, replace);
  },


  /* Fancy highlight: fancy spaces + fancy escape */
  fancyHl: function (text) {
    return this.fancySpaces(this.fancyEscape(text));
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

      if (op == 0) {
          if (removed) {
            textDiff += '<span class="diff-delete">' + PTL.editor.fancyEscape(removed) + '</span>'
            removed = "";
          }
          textDiff += PTL.editor.fancyEscape(text);
      } else if (op == 1) {
        if (removed) {
          // This is part of a substitution, not a plain insertion. We
          // will format this differently.
          textDiff += '<span class="diff-replace">' + PTL.editor.fancyEscape(text) + '</span>';
          removed = "";
        } else {
          textDiff += '<span class="diff-insert">' + PTL.editor.fancyEscape(text) + '</span>';
        }
      } else if (op == -1) {
        removed = text;
      }
    });

    if (removed) {
      textDiff += '<span class="diff-delete">' + PTL.editor.fancyEscape(removed) + '</span>';
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

  showActivity: function (force) {
    if ($("#xhr-error").is(':hidden')) {
      $("#xhr-activity").show();
    }
  },

  hideActivity: function () {
    $("#xhr-activity").hide();
  },

  updatePermalink: function (opts) {
    if (opts !== false) {
      // FIXME: We need a completely different way for getting view URLs in JS
      var urlStr = this.store ? this.store + '/translate/#unit=' :
                                this.directory + 'translate.html#unit=';
      // Translators: Permalink to the current unit in the editor.
      //    The first '%s' is the permalink URL.
      //    The second '%s' is the unit number.
      var thePermalink = interpolate(gettext('<a href="%s">Unit %s</a>'),
                                     [l(urlStr + PTL.editor.activeUid),
                                      PTL.editor.activeUid]);
    } else {
      var thePermalink = '';
    }

    $("#editor-permalink").html(thePermalink);
  },

  /*
   * Error handling
   */

  /* Displays error messages returned in XHR requests */
  displayError: function (msg) {
    if (msg) {
      this.hideActivity();
      $("#xhr-error span").text(msg).parent().stop(true, true).fadeIn(300).delay(2000).fadeOut(3500);
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
      if (xhr instanceof XMLHttpRequest) {
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
        if (this.checks.length) {
         reqData.checks = this.checks.join(",");
        }
        break;

      case "search":
        reqData.search = this.searchText;
        reqData.sfields = this.searchFields;
        break;

      case "suggestions":
        reqData.matchnames = 'hassuggestion'
        break;

      case "mysuggestions":
        reqData.matchnames = 'ownsuggestion'
        break;

      case "all":
        break;

      case "incomplete":
        reqData.unitstates = "untranslated,fuzzy";
        break;

      default:
        reqData.unitstates = this.filter;
        break;
    }

    return reqData;
  },


  /*
   * Unit navigation, display, submission
   */

  /* Gets the view units that refer to currentPage */
  getViewUnits: function (opts) {
    var extraData, reqData, viewUrl,
        defaults = {async: false, limit: 0, page: this.currentPage,
                    pager: false, withUid: false},
        urlStr = this.store ? this.store + '/view' : this.directory + 'view.html';
    // Merge passed arguments with defaults
    opts = $.extend({}, defaults, opts);

    // Extend URL if needed
    if (opts.limit != 0) {
      urlStr = urlStr + '/limit/' + limit;
    }
    viewUrl = l(urlStr);

    // Extra request variables specific to this function
    extraData = {page: opts.page};
    if (Object.size(this.meta) == 0) {
      extraData.meta = true;
    }
    if (opts.pager) {
      extraData.pager = opts.pager;
    }
    if (opts.withUid) {
      extraData.uid = this.activeUid;
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
        // Fill in metadata information if we don't have it yet
        if (Object.size(PTL.editor.meta) == 0 && data.meta) {
          PTL.editor.meta = data.meta;
        }

        // Receive pager in case we have asked for it
        if (opts.pager) {
          if (data.pager) {
            PTL.editor.hasResults = true;

            // Clear old data and add new results
            PTL.editor.pagesGot = {};
            PTL.editor.units = {};
            PTL.editor.updatePager(data.pager);
            // PTL.editor.fetchPages(false);
            if (data.uid) {
              PTL.editor.activeUid = data.uid;
            }
          }
        }

        // Store view units in the client
        if (data.units.length) {
          // Determine in which page we want to save units, as we may not
          // have specified it in the GET parameters — in that case, the
          // page number is specified within the response pager
          if (opts.withUid && data.pager) {
            var page = data.pager.number;
          } else {
            var page = opts.page;
          }

          PTL.editor.pagesGot[page] = [];

          // Copy retrieved units to the client
          $.each(data.units, function () {
            PTL.editor.units[this.id] = this;
            PTL.editor.pagesGot[page].push(this.id);
          });

          PTL.editor.hasResults = true;
        } else {
          PTL.editor.hasResults = false;
          $("table.translate-table").trigger("noResults");
        }
      },
      error: PTL.editor.error
    });
  },


  /* Builds view rows for units represented by 'uids' */
  buildRows: function (uids) {
    var _this, i, unit,
        cls = "even",
        even = true,
        rows = "";

    for (i=0; i<uids.length; i++) {
      _this = uids[i].id || uids[i];
      unit = this.units[_this];

      // Build row i
      rows += '<tr id="row' + _this + '" class="view-row ' + cls + '">';
      rows += this.tmpl.vUnit($, {data: {meta: this.meta,
                                         unit: unit}}).join("");
      rows += '</tr>';

      // Update odd/even class
      cls = even ? "odd" : "even";
      even = !even;
    }

    return rows;
  },


  /* Builds context rows for units passed as 'units' */
  buildCtxRows: function (units, extraCls) {
    var i, unit,
        cls = "even",
        even = true,
        rows = "";

    for (i=0; i<units.length; i++) {
      unit = units[i];

      // Build context row i
      rows += '<tr id="ctx' + unit.id + '" class="ctx-row ' + extraCls +
              ' ' + cls + '">';
      rows += this.tmpl.vUnit($, {data: {meta: this.meta,
                                         unit: unit}}).join("");
      rows += '</tr>';

      // Update odd/even class
      cls = even ? "odd" : "even";
      even = !even;
    }

    return rows;
  },


  /* Gets uids that should be displayed before/after 'uid' */
  getUidsBeforeAfter: function (uid) {
    var howMuch, i, m, prevNextL, tu,
        uids = {before: [], after: []},
        limit = parseInt((this.pager.per_page - 1) / 2),
        current = this.units[uid],
        prevNext = {prev: "before", next: "after"};

    for (m in prevNext) {
      tu = current;

      // Fill uids[before|after] with prev/next ids
      for (i=0; i<limit; i++) {
        if (tu[m] != undefined && tu[m] in this.units) {
          var tu = this.units[tu[m]];
          uids[prevNext[m]].push(tu.id);
        }
      }
    }

    // Only fill remaining rows if we have more units than the limit
    if (Object.size(this.units) > limit) {
      prevNextL = {prev: "after", next: "before"};

      for (m in prevNext) {
        // If we have less units that the limit, fill that in
        if (uids[prevNextL[m]].length < limit) {
          // Add (limit - length) units to uids[prevNext[m]]
          howMuch = limit - uids[prevNextL[m]].length;
          tu = this.units[uids[prevNext[m]][uids[prevNext[m]].length-1]];

          for (i=0; i<howMuch; i++) {
            if (tu[m] != undefined) {
              var tu = this.units[tu[m]];
              uids[prevNext[m]].push(tu.id);
            }
          }
        }
      }
    }

    uids.before.reverse();

    return uids;
  },


  /* Checks and fixes the linking between units */
  checkUnitsLinking: function () {
    var first, last, lastInPrevPage, p, pnP;

    for (p in this.pagesGot) {
      // Ensure we work with integers
      p = parseInt(p);

      // First and last units in this page
      first = this.pagesGot[p][0];
      last = this.pagesGot[p][this.pagesGot[p].length-1];
      // Check linking to the previous unit from the first unit in this page
      if (p > 1 && (!this.units[first].hasOwnProperty('prev') || this.units[first].prev == null)) {
        // We can only set the linking if the previous page
        // has already been fetched
        pnP = p - 1;
        if (pnP in this.pagesGot) {
          lastInPrevPage = this.pagesGot[pnP][this.pagesGot[pnP].length-1];
          $.extend(this.units[first], {prev: lastInPrevPage});
        }
      }

      // Check linking to the next unit from the last unit in this page
      if (p < this.pager.num_pages &&
          (!this.units[last].hasOwnProperty('next') || this.units[last].next == null)) {
        // We can only set the linking if the next page
        // has already been fetched
        pnP = p + 1;
        if (pnP in this.pagesGot) {
          $.extend(this.units[last], {next: this.pagesGot[pnP][0]});
        }
      }
    }
  },


  /* Sets the edit view for unit 'uid' */
  displayEditUnit: function (uid) {
    var uids, newTbody;

    // Ensure linking is correct before moving to a specific unit
    this.checkUnitsLinking();

    if (PTL.editor.hasResults) {
      // Fetch pages asynchronously — we already have the needed pages
      // so this will return units whenever it can
      this.fetchPages(true);

      // Get the actual editing widget and the surrounding view rows
      uids = this.getUidsBeforeAfter(uid);
      newTbody = this.buildRows(uids.before) +
                 this.getEditUnit(uid) +
                 this.buildRows(uids.after);

      this.reDraw(newTbody);
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


  /* Fetches more view unit pages in case they're needed */
  fetchPages: function (async) {
    var i,
        current = this.currentPage,
        candidates = [current, current + 1, current - 1],
        pages = [];

    // We will only fetch valid pages and pages that haven't
    // already been fetched
    for (i=0; i<candidates.length; i++) {
      if (candidates[i] <= this.pager.num_pages &&
          candidates[i] > 0 &&
          !(candidates[i] in this.pagesGot)) {
        pages.push(candidates[i]);
      }
    }

    // Do the actual fetching
    for (i=0; i<pages.length; i++) {
      this.getViewUnits({async: async, page: pages[i]});
    }
  },

  /* Updates the pager */
  updatePager: function (pager) {
    this.pager = pager;

    // If page number or num_pages has changed, redraw pager
    if (this.currentPage != pager.number ||
        this.currentNumPages != pager.num_pages) {
      this.currentPage = pager.number;
      this.currentNumPages = pager.num_pages;

      // Update UI elements
      $("#item-number").val(pager.number);
      $("#items-count").text(pager.num_pages);
    }
  },

  /* Creates a pager based on the current client data and the given uid */
  createPager: function (uid) {
    var newPager = this.pager;
    // In case the given uid is not within the current page,
    // calculate in which page it is
    if ($.inArray(uid, this.pagesGot[this.currentPage]) == -1) {
      var newPageNumber,
          i = this.currentPage,
          j = this.currentPage + 1,
          found = false;
      // Search uid within the pages the client knows of
      while (!found && (i > 0 || j <= this.pager.num_pages)) {
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
        newPager.number = newPageNumber;
      }
    }

    return newPager;
  },

  /* Loads the edit unit 'uid' */
  getEditUnit: function (uid) {
    var editor, editCtxRowBefore, editCtxRowAfter, editCtxWidgets, hasData,
        eClass = "edit-row",
        editUrl = l('/unit/edit/' + uid),
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
        PTL.editor.updatePager(PTL.editor.createPager(uid));

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

    eClass += this.units[uid].isfuzzy ? " fuzzy-unit" : "";

    hasData = ctx.before.length || ctx.after.length;
    editCtxWidgets = this.editCtxUI({hasData: hasData});
    editCtxRowBefore = editCtxWidgets[0];
    editCtxRowAfter = editCtxWidgets[1];

    editor = (PTL.editor.filter !== 'all' ?
              editCtxRowBefore + this.buildCtxRows(ctx.before, "before") : '') +
             '<tr id="row' + uid + '" class="' + eClass + '">' +
             widget + '</tr>' +
             (PTL.editor.filter !== 'all' ?
              this.buildCtxRows(ctx.after, "after") + editCtxRowAfter : '');

    this.activeUid = uid;

    return editor;
  },

  /* Pushes translation submissions and moves to the next unit */
  submit: function (e) {
    e.preventDefault();

    var reqData, submitUrl,
        uid = PTL.editor.activeUid,
        form = $("#captcha").ifExists() || $("#translate");

    submitUrl = l('/unit/submit/' + uid);

    // Serialize data to be sent and get required attributes for the request
    reqData = form.serializeObject();
    $.extend(reqData, PTL.editor.getReqData());

    $.ajax({
      url: submitUrl,
      type: 'POST',
      data: reqData,
      dataType: 'json',
      async: false,
      success: function (data) {
        if (data.captcha) {
          $.fancybox(data.captcha);
          $("#id_captcha_answer").focus();
        } else {
          // If it has been a successful submission, update the data
          // stored in the client
          PTL.editor.units[uid].isfuzzy = PTL.editor.isFuzzy();
          $("textarea[id^=id_target_f_]").each(function (i) {
            PTL.editor.units[uid].target[i].text = PTL.editor.cleanEscape($(this).val());
          });

          PTL.editor.loadNext(uid);
        }
      },
      error: PTL.editor.error
    });
  },

  /* Pushes translation suggestions and moves to the next unit */
  suggest: function (e) {
    e.preventDefault();

    var reqData, suggestUrl,
        uid = PTL.editor.activeUid,
        form = $("#captcha").ifExists() || $("#translate");

    suggestUrl = l('/unit/suggest/' + uid);

    // Serialize data to be sent and get required attributes for the request
    reqData = form.serializeObject();
    $.extend(reqData, PTL.editor.getReqData());

    $.ajax({
      url: suggestUrl,
      type: 'POST',
      data: reqData,
      dataType: 'json',
      async: false,
      success: function (data) {
        if (data.captcha) {
          $.fancybox(data.captcha);
          $("#id_captcha_answer").focus();
        } else {
          PTL.editor.loadNext(uid);
        }
      },
      error: PTL.editor.error
    });
  },

  /* Loads the next unit */
  loadNext: function (uid) {
    // FIXME: we can reuse the 'gotoPrevNext' function below for this purpose
    var newUid = parseInt(PTL.editor.units[uid].next);
    if (newUid) {
      var newHash = PTL.utils.updateHashPart("unit", newUid, ["page"]);
      $.history.load(newHash);
    } else {
      PTL.editor.displayError(gettext("Congratulations, you walked through all items"));
    }
  },

  /* Loads the editor with the next unit */
  gotoPrevNext: function (e) {
    e.preventDefault();
    var current = PTL.editor.units[PTL.editor.activeUid],
        prevNextMap = {previous: current.prev, next: current.next},
        newUid = prevNextMap[$(e.target).attr("class")];

    // Try loading the prev/next unit
    if (newUid != null) {
      var newHash = PTL.utils.updateHashPart("unit", parseInt(newUid), ["page"]);
      $.history.load(newHash);
    } else {
      if ($(e.target).attr("class") == 'previous') {
        PTL.editor.displayError(gettext("You reached the beginning of the list"));
      } else {
        PTL.editor.displayError(gettext("You reached the end of the list"));
      }
    }
  },


  /* Loads the editor with a specific unit */
  gotoUnit: function (e) {
    e.preventDefault();

    // Don't load anything if we're just selecting text
    if (PTL.editor.getSelectedText() != "") {
      return;
    }

    // Get clicked unit's uid from the row's id information and
    // try to load it
    var m = $(this).attr("id").match(/row([0-9]+)/);
    if (m) {
      var uid = parseInt(m[1]);
      var newHash = PTL.utils.updateHashPart("unit", uid, ["page"]);
      $.history.load(newHash);
    }
  },

  /* Loads the editor on a specific page */
  gotoPage: function (page) {
    // Only load the given page if it's within a valid page range
    if (page && !isNaN(page) && page > 0 &&
        page <= PTL.editor.pager.num_pages) {
      var newHash = PTL.utils.updateHashPart("page", page, ["unit"]);
      $.history.load(newHash);
    }
  },

  gotoFirstPage: function () {
    if (PTL.editor.currentNumPages > 0) {
      this.gotoPage(1);
    }
  },

  gotoLastPage: function () {
    if (PTL.editor.currentNumPages > 0) {
      this.gotoPage(PTL.editor.currentNumPages);
    }
  },

  gotoPrevPage: function () {
    if ((PTL.editor.currentNumPages > 0) && (this.currentPage > 1)) {
      this.gotoPage(this.currentPage - 1);
    }
  },

  gotoNextPage: function () {
    if ((PTL.editor.currentNumPages > 0) && (this.currentPage < PTL.editor.currentNumPages)) {
      this.gotoPage(this.currentPage + 1);
    }
  },

  /*
   * Units filtering
   */

  /* Gets the failing check options for the current query */
  getCheckOptions: function () {
    var opts,
        checksUrl = this.store ? l(this.store + '/checks/') : l(this.directory + "checks.html");

    $.ajax({
      url: checksUrl,
      async: false,
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
      var newHash = "filter=checks," + filterBy;
      $.history.load(newHash);
    }
  },

  /* Loads units based on filtering */
  filterStatus: function () {
    // this function can be executed in different contexts,
    // so using the full selector here
    var filterBy = $("#filter-status option:selected").val();

    // Filtering by failing checks
    if (filterBy == "checks") {
      // Get actual failing checks
      var optGroups = PTL.editor.getCheckOptions();

      // If there are any failing checks, add them in a dropdown
      if (optGroups.length) {
        var dropdown = '<div id="filter-checks">';
        dropdown += '<select name="filter-checks">';
        dropdown += '<option selected="selected" value="none">------</option>';

        $.each(optGroups, function () {
          dropdown += '<optgroup label="' + this.display_name + '">';
          $.each(this.checks, function () {
            dropdown += '<option value="' + this.name + '">' + this.display_name + ' (' + this.count + ')</option>';
          });
          dropdown += '</optgroup>';
        });

        dropdown += '</select></div>';

        $("#filter-status").first().after(dropdown);
      } else { // No results
        PTL.editor.displayError(gettext("No results."));
        $("#filter-status option[value=" + PTL.editor.filter + "]")
          .attr("selected", "selected");
      }
    } else { // Normal filtering options (untranslated, fuzzy...)
      $("#filter-checks").remove();
      if (!PTL.editor.preventNavigation) {
        var newHash = "filter=" + filterBy;
        $.history.load(newHash);
      }
    }
  },

  /* Generates the edit context rows' UI */
  editCtxUI: function (opts) {
    var defaults = {hasData: false, replace: false};
    opts = $.extend({}, defaults, opts);

    editCtxRowBefore = PTL.editor.tmpl.editCtx($, {data: {hasData: opts.hasData,
                                                          extraCls: 'before'}})
                                      .join("");
    editCtxRowAfter = PTL.editor.tmpl.editCtx($, {data: {hasData: opts.hasData,
                                                         extraCls: 'after'}})
                                     .join("");

    if (opts.replace) {
      $("tr.edit-ctx.before").replaceWith(editCtxRowBefore);
      $("tr.edit-ctx.after").replaceWith(editCtxRowAfter);
    }

    return [editCtxRowBefore, editCtxRowAfter];
  },

  /* Gets more context units */
  moreContext: function (initial) {
    var ctxUrl = l('/unit/context/' + PTL.editor.activeUid),
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
  search: function () {
    var newHash,
        text = $("#id_search").val();

    if (text) {
      var parsed = PTL.search.parse(text);
      newHash = "search=" + parsed;
    } else {
      newHash = PTL.utils.updateHashPart("filter", "all", ["search", "sfields"]);
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

    var uid = PTL.editor.activeUid,
        node = $("#extras-container"),
        timelineUrl = l("/unit/timeline/" + uid);

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

        if (data.timeline && uid === PTL.editor.activeUid) {
          if ($("#translator-comment").length) {
            $(data.timeline).hide().appendTo("#translator-comment")
                            .slideDown(1000, 'easeOutQuad');
          } else {
            $(data.timeline).hide().prependTo("#extras-container")
                            .slideDown(1000, 'easeOutQuad');
          }
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
      results[i].target = this.fancyHl(results[i].target);
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
    var src = this.meta.source_lang,
        tgt = this.meta.target_lang,
        sText = $($("input[id^=id_source_f_]").get(0)).val(),
        pStyle = this.meta.project_style,
        tmUrl = this.settings.tmUrl + src + "/" + tgt +
          "/unit/?source=" + encodeURIComponent(sText) + "&jsoncallback=?";

    if (!sText.length) {
        // No use in looking up an empty string
        return;
    }

    if (pStyle.length && pStyle != "standard") {
        tmUrl += '&style=' + this.meta.project_style;
    }

    // Always abort previous requests so we only get results for the
    // current unit
    if (this.tmReq != null) {
      this.tmReq.abort();
    }

    this.tmReq = $.jsonp({
      url: tmUrl,
      callback: '_jsonp' + PTL.editor.activeUid,
      dataType: 'jsonp',
      cache: true,
      success: function (data) {
        var uid = this.callback.slice(6);

        if (uid == PTL.editor.activeUid && data.length) {
          var filtered = PTL.editor.filterTMResults(data),
              name = gettext("amaGama server"),
              tm = PTL.editor.tmpl.tm($, {data: {meta: PTL.editor.meta,
                                                 suggs: filtered,
                                                 name: name}}).join("");

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
        url = l('/suggestion/reject/') + uid + '/' + suggId;

    $.post(url, {'reject': 1},
      function (data) {
        element.fadeOut(200, function () {
          $(this).remove();

          // Go to the next unit if there are no more suggestions left
          if (!$("#suggestions div[id^=suggestion]").length) {
            $("input.next").trigger("click");
          }
        });
      }, "json");
  },


  /* Accepts a suggestion */
  acceptSuggestion: function (e) {
    e.stopPropagation(); //we don't want to trigger a click on the text below
    var suggId = $(this).data("sugg-id"),
        element = $("#suggestion-" + suggId);
        uid = $('.translate-container #id_id').val(),
        url = l('/suggestion/accept/') + uid + '/' + suggId;

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

        // As in submissions, save current unit's status in the client
        $("textarea[id^=id_target_f_]").each(function (i) {
          PTL.editor.units[uid].target[i].text = PTL.editor.cleanEscape($(this).val());
        });
        PTL.editor.units[uid].isfuzzy = false;

        element.fadeOut(200, function () {
          $(this).remove();

          // Go to the next unit if there are no more suggestions left
          if (!$("#suggestions div[id^=suggestion]").length) {
            $("input.next").trigger("click");
          }
        });
      }, "json");
  },

  /* Clears the vote for a specific suggestion */
  clearVote: function (e) {
    e.stopPropagation(); //we don't want to trigger a click on the text below
    var element = $(this),
        voteId = element.data("vote-id"),
        url = l('/vote/clear/') + voteId;

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
        url = l('/vote/up/') + PTL.editor.activeUid + '/' + suggId;

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
        url = l('/qualitycheck/reject/') + uid + '/' + checkId;

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
    if (this.isSupportedTarget(provider.pairs, provider.targetLang)) {
      var _this = this;
      var sources = $(".translate-toolbar");
      $(sources).each(function () {
        var source = _this.normalizeCode($(this).parent().parent().find('.translation-text').attr("lang"));

        var ok;
        if (provider.validatePairs) {
          ok = _this.isSupportedPair(provider.pairs, source, provider.targetLang);
        } else {
          ok = _this.isSupportedSource(provider.pairs, source);
        }

        if (ok) {
          _this.addMTButton(this,
            provider.buttonClassName,
            provider.hint + ' (' + source.toUpperCase() + '&rarr;' + provider.targetLang.toUpperCase() + ')');
        }
      });
    }
  },

  /* Normalizes language codes in order to use them in MT services */
  normalizeCode: function (locale) {
      var clean = locale.replace('_', '-')
      var atIndex = locale.indexOf("@");
      if (atIndex != -1) {
        clean = clean.slice(0, atIndex);
      }
      return clean;
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

        areas.eq(j).val($("<div />").html(translation).text());
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
    var btn = '<a class="translate-lookup iframe ' + aClass + '">';
    btn += '<i class="icon-' + aClass + '" title="' + tooltip + '"></i></a>';
    $(container).first().prepend(btn);
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
      provider.hint + ' (' + source.toUpperCase() + ')');
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
    $.fancybox({
            "href": url,
            "type": "iframe",
            "autoScale": false,
            "transitionIn": 'none',
            "transitionOut": 'fade',
            "width": '75%',
            "height": '75%'
    });
    $("#fancybox-frame").css({'width': '100%', 'height': '100%'});
    linkObject.href = url;
    return false;
  }


  }; // PTL.editor

})(jQuery);
