(function ($) {

  window.PTL = window.PTL || {};

  // XXX: maybe this can go into its own file
  PTL.utils = {

    /* Gets current URL's hash */
    getHash: function (win) {
      var hash = ((win || window).location.hash).replace(/^#/, '');
      try {
        return $.browser.mozilla ? hash : decodeURIComponent(hash);
      } catch (error) {
        return hash;
      }
    },

    /* Updates current URL's hash */
    updateHashPart: function (part, newVal, replace) {
      var hash = this.getHash();
      if (!hash) {
        return part + "/" + newVal;
      }

      var parts = hash.split("/"),
          partIdx = parts.indexOf(part);
      if (partIdx == -1) {
        partIdx = parts.indexOf(replace);
      }

      if (partIdx > -1 ) {
        parts[partIdx] = part;
        parts[partIdx + 1] = newVal;
        return parts.join("/");
      }
      return hash + "/" + part + "/" + newVal;
    },
  };

  // XXX: Know of a better place for this?
  /* Returns the number (size) of properties of a given object */
  Object.size = function (obj) {
    var size = 0, key;
    for (key in obj) {
      if (obj.hasOwnProperty(key)) {
        size++;
      }
    }
    return size;
  };

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
    this.store = $("div#pootle_path").text();
    this.directory = $("div#directory").text();
    this.currentPage = 1;
    this.currentNumPages = 0;
    this.pagesGot = {};
    this.filter = "all";
    this.checks = [];
    this.ctxtGap = 0;
    this.keepState = false;

    this.isLoading = true;
    this.showActivity();

    /* Currently active search fields */
    this.searchFields = [];
    /* Valid search field options */
    this.searchOptions = ['source', 'target', 'notes', 'locations'];

    /* Regular expressions */
    this.cpRE = /^(<[^>]+>|\[n\|t]|\W$^\n)*(\b|$)/gm;
    this.escapeRE = /<[^<]*?>|\r\n|[\r\n\t&<>]/gm;
    this.searchRE = /^in:.+|\sin:.+/i;

    /* TM requests handler */
    this.tmReq = null;

    /* Differencer */
    this.differencer = new diff_match_patch();

    /* Compile templates */
    this.tmpl = {vUnit: $.template($("#view_unit").html()),
                 tm: $.template($("#tm_suggestions").html())}

    /* Set initial focus on page load */
    this.focused = $(".translate-original-focus textarea").get(0);

    /*
     * Bind event handlers
     */

    /* Fuzzy / unfuzzy */
    $("textarea.translation").live("keyup blur", function () {
      if (!PTL.editor.keepState &&
          $(this).attr("defaultValue") != $(this).val()) {
        PTL.editor.ungoFuzzy();
      }
    });
    $("input.fuzzycheck").live("click", function () {
      if (PTL.editor.isFuzzy()) {
        PTL.editor.doFuzzyArea();
      } else {
        PTL.editor.undoFuzzyArea();
      }
    });

    /* Suggest / submit */
    $(".switch-suggest-mode a").live("click", function () {
      PTL.editor.toggleSuggestMode();
      return false;
    });

    /* Update focus when appropriate */
    $(".focusthis").live("focus", function (e) {
      PTL.editor.focused = e.target;
    });

    /* Write TM results, special chars... into the currently focused element */
    $(".writetm, .writespecial, .translate-full .highlight-escape, .translate-full .highlight-html").live("click", this.copyText);

    /* Copy original translation */
    $("a.copyoriginal").live("click", function () {
      var sources = $(".translation-text", $(this).parent().parent().parent());
      PTL.editor.copyOriginal(sources);
    });
    $("div.suggestion").live("click", function () {
      // Don't copy if text has been selected
      if (PTL.editor.getSelectedText() != "") {
        return;
      }
      var sources = $(".suggestion-translation", this);
      PTL.editor.copyOriginal(sources);
    });

    /* Editor navigation/submission */
    $("table.translate-table").live("editor_ready", this.ready);
    $("tr.view-row").live("click", this.gotoUnit);
    $("input#item-number").live("keypress", function (e) {
        // Perform action only when the 'Enter' key is pressed
        if (e.keyCode == 13) {
          PTL.editor.gotoPage();
        }
    });
    $("input.submit, input.suggest").live("click", this.processSubmit);
    $("input.previous, input.next").live("click", this.gotoPrevNext);
    $("#suggestion-container .rejectsugg").live("click", this.rejectSuggestion);
    $("#suggestion-container .acceptsugg").live("click", this.acceptSuggestion);
    $("#translate-checks-block .rejectcheck").live("click", this.rejectCheck);

    /* Filtering */
    $("div#filter-status select").live("change", this.filterStatus);
    $("div#filter-checks select").live("change", this.filterChecks);
    $("a.morecontext").live("click", this.getMoreContext);

    /* Search */
    $("input#id_search").live("keypress", function (e) {
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
    shortcut.add('ctrl+shift+u', function () {
      $("input#item-number").focus().select();
    });
    shortcut.add('ctrl+shift+s', function () {
      $("#id_search").focus().select();
    });
    $("#id_search").focus(function() {
      $(this).attr("focused", true);
    });
    $("#id_search").blur(function() {
      $(this).attr("focused", "");
    });
    shortcut.add('escape', function () {
      if ($("#id_search").attr("focused")) {
        $("#id_search").blur();
      }
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

      $.ajax({
        url: m('js/mt/' + backend + '.js'),
        async: false,
        dataType: 'script',
        success: function () {
          setTimeout(function () {
            PTL.editor.mt[backend].init();
          }, 0);
          $("table.translate-table").live("mt_ready",
                                          PTL.editor.mt[backend].ready);
        }
      });
    });

    /* History support */
    setTimeout(function () {
      $.history.init(function (hash) {
        var parts = hash.split("/");

        switch (parts[0]) {

          /* Load a specific unit based on its uid */
          case "unit":
            var uid = parseInt(parts[1]);

            if (uid && !isNaN(uid)) {
              // Take care when we want to access a unit directly
              // from a permalink
              if (PTL.editor.activeUid != uid &&
                  PTL.editor.units[uid] == undefined) {
                PTL.editor.activeUid = uid;
                PTL.editor.getViewUnits({pager: true, withUid: true});
              }
              // Now it's safe to actually load the unit
              PTL.editor.displayEditUnit(uid);
            }

            break;

          /* Filter units based on specific criterias */
          case "filter":
            // Save previous states in case there are no results
            PTL.editor.prevChecks = PTL.editor.checks;
            PTL.editor.prevFilter = PTL.editor.filter;

            // Set current state
            PTL.editor.checks = parts[1] == "checks" ? parts[2].split(',') : [];
            PTL.editor.filter = parts[1];

            unit_idx = parts.indexOf('unit');
            if (unit_idx > -1) {
              var uid = parseInt(parts[unit_idx+1])
              if (uid && !isNaN(uid)) {
                PTL.editor.activeUid = uid;
                PTL.editor.getViewUnits({pager: true, withUid: true});
                PTL.editor.displayEditUnit(PTL.editor.activeUid);
                break;
              }
            } else {
              page_idx = parts.indexOf('page');
              if (page_idx > -1) {
                var p = parseInt(parts[page_idx + 1]);
                if (p && !isNaN(p) && p > 0) {
                  PTL.editor.getViewUnits({pager: true, page: p});
                  if (PTL.editor.hasResults) {
                    var which = parseInt(PTL.editor.pagesGot[p].length / 2);
                    var uid = PTL.editor.pagesGot[p][which];
                    PTL.editor.activeUid = uid;
                    PTL.editor.displayEditUnit(uid);
                    break;
                  }
                }
              }
            }
            // Load units based on this filtering criteria
            PTL.editor.getViewUnits({pager: true});
            PTL.editor.displayEditUnit(PTL.editor.activeUid);
            break;

          /* Perform search and parse search fields */
          case "search":
            PTL.editor.filter = parts[0];

            // Parse search fields from query string
            var params, pair, key, val,
                sfields = [],
                qs = parts[1].split("?");

            // Search text is all the text before "?"
            PTL.editor.searchText = qs[0];

            // Parse query parameters and detect fields
            params = qs[1] == undefined ? [] : qs[1].split("&");
            $.each(params, function (i, keyVal) {
              pair = keyVal.split("=");
              key = pair[0];
              val = pair[1];
              // We will only consider keys that match 'sfields'
              if (key == 'sfields') {
                sfields.push(val);
              }
            });
            PTL.editor.searchFields = sfields;

            // Finally, load the units that match this search
            PTL.editor.getViewUnits({page: 1, pager: true});
            PTL.editor.displayEditUnit(PTL.editor.activeUid);

            break;

          /* Load pages directly */
          case "page":
            var p = parseInt(parts[1]);

            if (p && !isNaN(p) && p > 0) {
              if (!(p in PTL.editor.pagesGot)) {
                PTL.editor.getViewUnits({pager: true, page: p});
              }
              // If there are no results for page p, it may be an
              // invalid page number
              if (PTL.editor.hasResults) {
                var which = parseInt(PTL.editor.pagesGot[p].length / 2);
                var uid = PTL.editor.pagesGot[p][which];
                PTL.editor.activeUid = uid;
                PTL.editor.displayEditUnit(uid);
              }
            }

            break;

          /* Load the first page in the current view as default */
          default:
            PTL.editor.getViewUnits({pager: true});
            PTL.editor.displayEditUnit(PTL.editor.activeUid);
        }
      }, {'unescape': true});
    }, 1000);

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

    PTL.editor.isLoading = false;
    PTL.editor.hideActivity();
  },


  /*
   * Text utils
   */

  escapeUnsafeRegexSymbols: function (s) {
    r = "\\.+*?[^]$(){}=!<>¦:"; 
    for (i = 0; i < s.length; i++) { 
      s = s.replace(new RegExp("\\" + r.charAt(i),"g"), "\\" + r.charAt(i));
    }
    return s;
  },

  makeRegexForMultipleWords: function (s) {
    var w = s.split(' ');
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
      sel.push(selMap[field]);
    });

    // By default we search source and target texts
    if (!sel.length) {
      sel = [selMap['source'], selMap['target']];
    }

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
    var text, element, start;

    // Determine which text we need
    if ($(".tm-translation", this).length) {
      text = $(".tm-translation", this).text();
    } else {
      text = $(this).text();
    }

    element = $(PTL.editor.focused);
    start = element.caret().start + text.length;

    element.val(element.caret().replace(text));
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

  /* Escapes HTML tags */
  escapeHtml: function (s) {
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").
             replace(/>/g,"&gt;").replace(/\n/,"<br/>");
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
              '\t': escapeHl.replace(/%s/, '\\t') + '\t',
              '&': '&amp;',
              '<': '&lt;',
              '>': '&gt;'
            }

        replaced = submap[match];

        if (replaced == undefined) {
            replaced = htmlHl.replace(/%s/, match.slice(1, match.length-1));
        }

        return replaced;
    }

    var orig = text,
        matches = text.match(this.escapeRE);

    for (var i in matches) {
      orig = orig.replace(matches[i], replace(matches[i]))
    }

    return orig;
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
    // TODO: i18n
    var msg = "";

    if (xhr.status == 0) {
      msg = "Error while connecting to the server.";
    } else if (xhr.status == 500) {
      msg = "Server error.";
    } else if (s == "timeout") {
      msg = "Server seems down, try again later.";
    } else {
      // Since we use jquery-jsonp, we must differentiate between
      // the passed arguments
      if (xhr instanceof XMLHttpRequest) {
        msg = $.parseJSON(xhr.responseText);
      } else {
        msg = "Unknown error.";
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
         reqData.matchnames = this.checks.join(",");
        }
        break;

      case "search":
        reqData.search = this.searchText;

        // Override defaults if any fields have been specified
        if (this.searchFields.length) {
          reqData.sfields = this.searchFields;
        } else {
          reqData.sfields = ["source", "target"];
        }
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
          } else { // No results
            PTL.editor.hasResults = false;
            // TODO: i18n
            PTL.editor.displayError("No results.");

            // Restore previous status
            PTL.editor.checks = PTL.editor.prevChecks;
            PTL.editor.filter = PTL.editor.prevFilter;
            $("#filter-status option[value=" + PTL.editor.filter + "]")
              .attr("selected", "selected");
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
          // TODO: i18n
          PTL.editor.displayError("No results.");
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
  buildCtxtRows: function (units) {
    var i, unit,
        cls = "even",
        even = true,
        rows = "";

    for (i=0; i<units.length; i++) {
      unit = units[i];

      // Build context row i
      rows += '<tr id="ctxt' + unit.id + '" class="context-row ' + cls + '">';
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

    where.append(newTbody);

    // We are ready, call the ready handlers
    $(tTable).trigger("editor_ready");
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
      $("input#item-number").val(pager.number);
      $("span#items-count").text(pager.num_pages);
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
          j = this.currentPage,
          found = false;

      // Search uid within the pages the client knows of
      while (!found && (i > 0 || j <= this.pager.num_pages)) {
        if ($.inArray(uid, this.pagesGot[i]) != -1) {
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
    var editor,
        eClass = "edit-row",
        editUrl = l('/unit/edit/' + uid),
        reqData = this.getReqData(),
        widget = '',
        ctxt = {before: [], after: []};

    $.ajax({
      url: editUrl,
      async: false,
      data: reqData,
      dataType: 'json',
      success: function (data) {
        widget = data['editor'];

        // Update pager in case it's needed
        PTL.editor.updatePager(PTL.editor.createPager(uid));

        if (data.ctxt) {
          PTL.editor.ctxtGap = 2;
          ctxt.before = data.ctxt.before;
          ctxt.after = data.ctxt.after;
        }
      },
      error: PTL.editor.error
    });

    eClass += this.units[uid].isfuzzy ? " fuzzy-unit" : "";
    // TODO: i18n
    editor = (ctxt.before.length ? '<tr class="more-context before"><td colspan="2"><a class="morecontext">Show more context rows</a></td></tr>' : '') +
             this.buildCtxtRows(ctxt.before) +
             '<tr id="row' + uid + '" class="' + eClass + '">' +
             widget + '</tr>' +
             this.buildCtxtRows(ctxt.after) +
             (ctxt.after.length ? '<tr class="more-context after"><td colspan="2"><a class="morecontext">Show more context rows</a></td></tr>' : '');

    this.activeUid = uid;

    return editor;
  },


  /* Pushes submissions or suggestions and moves to the next unit */
  processSubmit: function (e, typeClass) {
    e.preventDefault();

    var formId, reqData, submitUrl, type,
        uid = PTL.editor.activeUid,
        typeMap = {submit: "submission", suggest: "suggestion"};

    // Detect whether it's being called from a normal submit or
    // from a captcha
    if (typeClass == undefined) {
      typeClass = $(e.target).attr("class");
      formId = "translate";
    } else {
      formId = "captcha";
    }

    type = typeMap[typeClass];
    submitUrl = l('/unit/process/' + uid + '/' + type);

    // Serialize data to be sent and get required attributes for the request
    reqData = $("form#" + formId).serializeObject();
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
          $("input#id_captcha_answer").focus();
        } else {
          // If it has been a successful submission, update the textarea
          // contents as well as the fuzzy status
          if (type == 'submission') {
            PTL.editor.units[uid].isfuzzy = PTL.editor.isFuzzy();
            $("textarea[id^=id_target_f_]").each(function (i) {
              PTL.editor.units[uid].target[i].text = $(this).val();
            });
          }

          // Try loading the next unit
          var newUid = parseInt(PTL.editor.units[uid].next);
          if (newUid) {
            var newHash = PTL.utils.updateHashPart("unit", newUid, "page");
            $.history.load(newHash);
          } else {
            // TODO: i18n
            PTL.editor.displayError("Congratulations, you walked through all items");
          }
        }
      },
      error: PTL.editor.error
    });
  },


  /* Loads the editor with the next unit */
  gotoPrevNext: function (e) {
    e.preventDefault();
    var current = PTL.editor.units[PTL.editor.activeUid],
        prevNextMap = {previous: current.prev, next: current.next},
        newUid = prevNextMap[$(e.target).attr("class")];

    // Try loading the prev/next unit
    if (newUid != null) {
      var newHash = PTL.utils.updateHashPart("unit", parseInt(newUid), "page");
      $.history.load(newHash);
    } else {
      if ($(e.target).attr("class") == 'previous') {
        // TODO: i18n
        PTL.editor.displayError("You reached the beginning of the list");
      } else {
        // TODO: i18n
        PTL.editor.displayError("You reached the end of the list");
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
      var newHash = PTL.utils.updateHashPart("unit", uid, "page");
      $.history.load(newHash);
    }
  },


  /* Loads the editor on a specific page */
  gotoPage: function () {
    var page = parseInt($("input#item-number").val());

    // Only load the given page if it's within a valid page range
    if (page && !isNaN(page) && page > 0 &&
        page <= PTL.editor.pager.num_pages) {
      var newHash = PTL.utils.updateHashPart("page", page, "unit");
      $.history.load(newHash);
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
        opts = data.checks;
      },
      error: PTL.editor.error
    });

    return opts;
  },

  /* Loads units based on checks filtering */
  filterChecks: function () {
    var filterBy = $("option:selected", this).val();

    if (filterBy != "none") {
      var newHash = "filter/checks/" + filterBy;
      $.history.load(newHash);
    }
  },

  /* Loads units based on filtering */
  filterStatus: function () {
    var filterBy = $("option:selected", this).val();

    // Filtering by failing checks
    if (filterBy == "checks") {
      // Get actual failing checks
      var opts = PTL.editor.getCheckOptions();

      // If there are any failing checks, add them in a dropdown
      if (opts.length) {
        var dropdown = '<div id="filter-checks" class="toolbar-item">';
        dropdown += '<select name="filter-checks">';
        dropdown += '<option selected="selected" value="none">------</option>';
        $.each(opts, function () {
          dropdown += '<option value="' + this.name + '">' + this.text + '</option>';
        });
        dropdown += '</select></div>';
        $("div#filter-status").first().after(dropdown);
      } else { // No results
        // TODO: i18n
        PTL.editor.displayError("No results.");
        $("#filter-status option[value=" + PTL.editor.filter + "]")
          .attr("selected", "selected");
      }
    } else { // Normal filtering options (untranslated, fuzzy...)
      $("div#filter-checks").remove();
      var newHash = "filter/" + filterBy;
      $.history.load(newHash);
    }
  },

  /* Gets more context units */
  getMoreContext: function () {
    var ctxtUrl = l('/unit/context/' + PTL.editor.activeUid);
        reqData = {gap: PTL.editor.ctxtGap};

    $.ajax({
      url: ctxtUrl,
      async: false,
      dataType: 'json',
      data: reqData,
      success: function (data) {
        // As we now have got more context rows, increase its gap
        PTL.editor.ctxtGap += 2;

        // Create context rows HTML
        var before = PTL.editor.buildCtxtRows(data.ctxt.before);
        var after = PTL.editor.buildCtxtRows(data.ctxt.after);

        // Append context rows to their respective places
        var ctxtRows = $("tr.context-row");
        ctxtRows.first().before(before);
        ctxtRows.last().after(after);
      },
      error: PTL.editor.error
    });
  },


  /*
   * Search
   */

  /* Parses search text to detect any given fields */
  parseSearch: function (text) {
    var urlFields = [],
        parsed = text;

    // Check if there are fields specified within the search text
    if (this.searchRE.test(text)) {
      var opt,
          removeParts = [],
          parts = text.split(" ");

      $.each(parts, function (i, part) {
        if (PTL.editor.searchRE.test(part)) {
          opt = part.split(":")[1];

          // Only consider valid fields
          if ($.inArray(opt, PTL.editor.searchOptions) > -1) {
            urlFields.push({name: 'sfields', value: opt});
          }

          // If it's an invalid field name, discard it from the search text
          removeParts.push(i);
        }
      });

      // Remove parsed fields from the original array.
      // It has to be done in reverse order for not clashing with indexes.
      $.each(removeParts.reverse(), function (i, j) {
        parts.splice(j, 1);
      });

      // Join unparsed remaining text, as this will be the actual search text
      parsed = encodeURIComponent(parts.join(" "));
    } else {
      // There were no fields specified within the text so we use the dropdown
      $("div.advancedsearch input:checked").each(function () {
        urlFields.push({name: 'sfields', value: $(this).val()});
      });
    }

    // If any fields have been chosen, append them to the resulting URL
    if (urlFields.length) {
      parsed += "?" + $.param(urlFields);
    }

    return parsed;
  },


  /* Loads the search view */
  search: function () {
    var text = $("input#id_search").val();
    if (text) {
      var parsed = this.parseSearch(text),
          newHash = "search/" + parsed;
      $.history.load(newHash);
    }
  },


  /*
   * User and TM suggestions
   */

  /* Filters TM results and does some processing (add diffs, extra texts...) */
  filterTMResults: function (results) {
    // FIXME: this just retrieves the first four results
    // we could limit based on a threshold too.
    // FIXME: use localized 'N% match' format string
    var source = $("[id^=id_source_f_]").first().val(),
        filtered = [];

    for (var i=0; i<results.length && i<3; i++) {
      results[i].source = this.doDiff(source, results[i].source);
      results[i].target = this.fancyEscape(results[i].target);
      results[i].qTitle = Math.round(results[i].quality) + '% match';
      filtered.push(results[i]);
    }

    return filtered;
  },


  /* Gets TM suggestions from amaGama */
  getTMUnits: function () {
    var src = this.meta.source_lang,
        tgt = this.meta.target_lang,
        stext = $($("input[id^=id_source_f_]").get(0)).val(),
        tmUrl = this.settings.tmUrl + src + "/" + tgt +
          "/unit/" + encodeURIComponent(stext) + "?jsoncallback=?";

    // Always abort previous requests so we only get results for the
    // current unit
    if (this.tmReq != null) {
      this.tmReq.abort();
    }

    // We use $.jsonp here because jQuery's current jsonp methods don't
    // accept error callbacks nor aborting requests
    this.tmReq = $.jsonp({
      url: tmUrl,
      callback: '_jsonp' + PTL.editor.activeUid,
      dataType: 'jsonp',
      success: function (data) {
        var uid = this.callback.slice(6);

        if (uid == PTL.editor.activeUid && data.length > 0) {
          var filtered = PTL.editor.filterTMResults(data),
          // TODO: i18n
              name = "amaGama server",
              tm = PTL.editor.tmpl.tm($, {data: {meta: PTL.editor.meta,
                                                 suggs: filtered,
                                                 name: name}}).join("");

          // Append results
          $("div#suggestion-container").append(tm);
          $("div#amagama_results").animate({height: 'show'}, 1000,
                                           'easeOutQuad');
        }
      },
      error: PTL.editor.error
    });
  },


  /* Rejects a suggestion */
  rejectSuggestion: function () {
    var element = $(this).parent(),
        uid = $('.translate-container input#id_id').val(),
        suggId = $(this).siblings("input.suggid").val(),
        url = l('/suggestion/reject/') + uid + '/' + suggId;

    $.post(url, {'reject': 1},
      function (data) {
        element.fadeOut(200, function () {
          $(this).remove();

          // Go to the next unit if there are no more suggestions left
          if (!$("div#suggestion-container div[id^=suggestion]").length) {
            $("input.next").trigger("click");
          }
        });
      }, "json");
  },


  /* Accepts a suggestion */
  acceptSuggestion: function () {
    var element = $(this).parent(),
        uid = $('.translate-container input#id_id').val(),
        suggId = $(this).siblings("input.suggid").val(),
        url = l('/suggestion/accept/') + uid + '/' + suggId;

    $.post(url, {'accept': 1},
      function (data) {
        // Update target textareas
        $.each(data.newtargets, function (i, target) {
          $("textarea#id_target_f_" + i).val(target).focus();
        });

        // Update remaining suggestion's diff
        $.each(data.newdiffs, function (suggId, sugg) {
          $.each(sugg, function (i, target) {
             $("#suggdiff-" + suggId + "-" + i).html(target);
          });
        });

        // As in submissions, save current unit's status in the client
        $("textarea[id^=id_target_f_]").each(function (i) {
          PTL.editor.units[uid].target[i].text = $(this).val();
        });
        PTL.editor.units[uid].isfuzzy = false;

        element.fadeOut(200, function () {
          $(this).remove();

          // Go to the next unit if there are no more suggestions left
          if (!$("div#suggestion-container div[id^=suggestion]").length) {
            $("input.next").trigger("click");
          }
        });
      }, "json");
  },


  /* Rejects a quality check marking it as false positive */
  rejectCheck: function () {
    var element = $(this).parent(),
        checkId = $(this).siblings("input.checkid").val(),
        uid = $('.translate-container input#id_id').val(),
        url = l('/qualitycheck/reject/') + uid + '/' + checkId;

    $.post(url, {'reject': 1},
      function (data) {
        element.fadeOut(200, function () {
          $(this).remove();
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
  addMTButton: function (aClass, imgFn, tooltip) {
      var btn = '<a class="translate-mt ' + aClass + '">';
      btn += '<img src="' + imgFn + '" title="' + tooltip + '" /></a>';
      $("div.translate-toolbar").first().prepend(btn);
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


  collectArguments: function (substring) {
    if (substring == '%%') {
      return '%%';
    }

    // FIXME: what do these variables do here?
    // and why are they in the global scope?
    argument_subs[pos] = substring;
    substitute_string = "__" + pos + "__";
    pos = pos + 1;

    return substitute_string;
  }

  }; // PTL.editor

})(jQuery);
