(function ($) {
  window.PTL = window.PTL || {};

  // XXX: Know of a better place for this?
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

  /*
   * Initializes the editor
   */
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
    this.currentPage = 1;
    this.pagesGot = {};
    this.filter = "all";
    this.checks = [];
    this.ctxtGap = 0;
    this.keepState = false;
    this.cpRE = new RegExp("^(<[^>]+>|\\[n\|t]|\\W$^\\n)*(\\b|$)", "gm");
    this.escapeRE = new RegExp("<[^<]*?>|\\r\\n|[\\r\\n\\t&<>]", "gm");

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

    /* Collapsing */
    $(".collapse").live("click", function (e) {
      e.preventDefault();
      $(this).siblings(".collapsethis").slideToggle("fast");
      if ($("textarea", $(this).next("div.collapsethis")).length) {
        $("textarea", $(this).next("div.collapsethis")).focus();
      }
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
      // to prevent the click event which occurs in Firefox but not in Chrome (and not in IE)
      if (e && e.preventDefault) {
        e.preventDefault();
      }

      // prevent automatic unfuzzying on keyup
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

    /* XHR activity indicator */
    $(document).ajaxStart(function () {
      setTimeout(function () {
        $("#xhr-error").hide();
        if ($.active > 0) {
          $("#xhr-activity").show();
        }
      }, 3000);
    });
    $(document).ajaxStop(function () {
      $("#xhr-activity").hide();
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
          $("table.translate-table").live("mt_ready", PTL.editor.mt[backend].ready);
        }
      });
    });

    /* History support */
    setTimeout(function () {
      $.history.init(function (hash) {
        var parts = hash.split("/");
        switch (parts[0]) {
          case "unit":
            var uid = parseInt(parts[1]);
            if (uid && !isNaN(uid)) {
              // Take care when we want to access a unit directly from a permalink
              if (PTL.editor.activeUid != uid &&
                  PTL.editor.units[uid] == undefined) {
                PTL.editor.activeUid = uid;
                PTL.editor.getMeta(true);
              }
              PTL.editor.displayEditUnit(uid);
            }
            break;
          case "filter":
            // Save previous states in case there are no results
            PTL.editor.prevChecks = PTL.editor.checks;
            PTL.editor.prevFilter = PTL.editor.filter;
            PTL.editor.checks = parts[1] == "checks" ? parts[2].split(',') : [];
            PTL.editor.filter = parts[1];
            PTL.editor.getMeta(false);
            PTL.editor.displayEditUnit(PTL.editor.activeUid);
            break;
          case "search":
            PTL.editor.filter = parts[0];
            PTL.editor.searchText = parts[1];
            PTL.editor.getMeta(false);
            PTL.editor.displayEditUnit(PTL.editor.activeUid);
            break;
          case "page":
            var p = parseInt(parts[1]);
            if (p && !isNaN(p)) {
              if (!(p in PTL.editor.pagesGot)) {
                PTL.editor.getViewUnits(false, p);
              }
              var which = parseInt(PTL.editor.pagesGot[p].length / 2);
              var uid = PTL.editor.pagesGot[p][which];
              PTL.editor.getMeta(true);
              PTL.editor.displayEditUnit(uid);
            }
            break;
          default:
            PTL.editor.getMeta(false);
            PTL.editor.displayEditUnit(PTL.editor.activeUid);
        }
      }, {'unescape': true});
    }, 1000);

  },

  /*
   * Stuff to be done when the editor is ready
   */
  ready: function () {
    var maxheight = $(window).height() * 0.3;
    $('textarea.expanding').TextAreaExpander('10', maxheight);
    $(".focusthis").get(0).focus();
    PTL.editor.hlSearch();
    PTL.editor.hlTerms();
    PTL.editor.getTMUnits();
    $("table.translate-table").trigger("mt_ready");
  },

  /*
   * Highlights search results
   */
  hlSearch: function () {
    var hl = PTL.editor.filter == "search" ? PTL.editor.searchText : "";
    var selMap = {notes: "div.developer-comments",
                  locations: "div.translate-locations",
                  source: "td.translate-original, div.original div.translation-text",
                  target: "td.translate-translation"};
    var sel = [];
    $("div.advancedsearch input:checked").each(function () {
     sel.push(selMap[$(this).val()]);
    });
    $(sel.join(", ")).highlightRegex(new RegExp(hl, "i"));
  },

  /*
   * Highlights matching terms in the source text.
   */
  hlTerms: function () {
    var term;
    $(".tm-original").each(function () {
      term = $(this).text();
      $("div.original .translation-text").highlightRegex(new RegExp(term, "g"));
    });
  },

  /*
   * Copies text into the focused textarea
   */
  copyText: function (e) {
    if ($(".tm-translation", this).length) {
      var text = $(".tm-translation", this).text();
    } else {
      var text = $(this).text();
    }
    var element = $(PTL.editor.focused);
    var start = element.caret().start + text.length;
    element.val(element.caret().replace(text));
    element.caret(start, start);
  },

  /*
   * Copies source text(s) into the target textarea(s)
   */
  copyOriginal: function (sources) {
    var cleanSources = [];
    $.each(sources, function (i) {
      cleanSources[i] = $(this).text();
    });

    var targets = $("[id^=id_target_f_]");
    if (targets.length) {
      var max = cleanSources.length - 1;
      for (var i=0; i<targets.length; i++) {
        var newval = cleanSources[i] || cleanSources[max];
        $(targets.get(i)).val(newval);
      }
      var active = $(targets).get(0);
      active.focus();
      PTL.editor.goFuzzy();
      /* Place cursor at start of target text */
      PTL.editor.cpRE.exec($(active).val());
      var i = PTL.editor.cpRE.lastIndex;
      $(active).caret(i, i);
      PTL.editor.cpRE.lastIndex = 0;
    }
  },

  /*
   * Gets selected text
   */
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

  /*
   * Fuzzying / unfuzzying functions
   */
  doFuzzyArea: function () {
    $("tr.edit-row").addClass("fuzzy-unit");
  },

  undoFuzzyArea: function () {
    $("tr.edit-row").removeClass("fuzzy-unit");
  },

  doFuzzyBox: function () {
    $("input.fuzzycheck").attr("checked", "checked");
  },

  undoFuzzyBox: function () {
    $("input.fuzzycheck").removeAttr("checked");
  },

  goFuzzy: function () {
    if (!this.isFuzzy()) {
      this.keepState = true;
      this.doFuzzyArea();
      this.doFuzzyBox();
    }
  },

  ungoFuzzy: function () {
    if (this.isFuzzy()) {
      this.keepState = true;
      this.undoFuzzyArea();
      this.undoFuzzyBox();
    }
  },

  isFuzzy: function () {
    return $("input.fuzzycheck").attr("checked");
  },

  /*
   * Suggest / submit mode functions
   */
  doSuggestMode: function () {
    $("table.translate-table").addClass("suggest-mode");
  },

  undoSuggestMode: function () {
    $("table.translate-table").removeClass("suggest-mode");
  },

  isSuggestMode: function () {
    return $("table.translate-table").hasClass("suggest-mode");
  },

  toggleSuggestMode: function () {
    if (this.isSuggestMode()) {
      this.undoSuggestMode();
    } else {
      this.doSuggestMode();
    }
  },

  /*
   * Displays error messages returned in XHR requests
   */
  displayError: function (msg) {
    if (msg) {
      $("#xhr-activity").hide();
      $("#xhr-error span").text(msg).parent().show().fadeOut(3500);
    }
  },

  /*
   * Handles XHR errors
   */
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
   * Gets common request data
   */
  getReqData: function () {
    var reqData = {filter: this.filter};
    if (this.filter == "checks" && this.checks.length) {
      reqData.checks = this.checks.join(",");
    }
    if (this.filter == "search") {
      reqData.search = this.searchText;
      reqData.sfields = [];
      $("div.advancedsearch input:checked").each(function () {
        reqData.sfields.push($(this).val());
      });
    }
    return reqData;
  },


  /*
   * Unit navigation, display, submission
   */

  /* Retrieves the metadata used for this query */
  getMeta: function (withUid) {
    var append = withUid ? this.activeUid : "";
    var metaUrl = l(this.store + "/meta/" + append);
    var reqData = this.getReqData();
    $.ajax({
      url: metaUrl,
      async: false,
      data: reqData,
      dataType: 'json',
      success: function (data) {
        if (data.pager) {
          PTL.editor.hasResults = true;
          PTL.editor.meta = data.meta;
          PTL.editor.pagesGot = {};
          PTL.editor.units = {};
          PTL.editor.updatePager(data.pager);
          PTL.editor.fetchPages(false);
          if (data.uid) {
            PTL.editor.activeUid = data.uid;
          }
        } else { // No results
          PTL.editor.hasResults = false;
          // TODO: i18n
          PTL.editor.displayError("No results.");
          PTL.editor.checks = PTL.editor.prevChecks;
          PTL.editor.filter = PTL.editor.prevFilter;
          $("#filter-status option[value=" + PTL.editor.filter + "]")
            .attr("selected", "selected");
        }
      }
    });
  },

  /* Gets the view units that refer to currentPage */
  getViewUnits: function (async, page, limit) {
    var async = async == undefined ? false : async;
    var page = page == undefined ? this.currentPage : page;
    var limit = limit == undefined ? 0 : limit;
    var urlStr = this.store + '/view';
    urlStr = limit ? urlStr + '/limit/' + limit : urlStr;
    var viewUrl = l(urlStr);
    var reqData = $.extend({page: page}, this.getReqData());
    $.ajax({
      url: viewUrl,
      data: reqData,
      dataType: 'json',
      async: async,
      success: function (data) {
        PTL.editor.pagesGot[page] = [];
        $.each(data.units, function () {
          PTL.editor.units[this.id] = this;
          PTL.editor.pagesGot[page].push(this.id);
        });
      },
      error: PTL.editor.error
    });
  },

  /* Builds view rows for units represented by 'uids' */
  buildRows: function (uids) {
    var cls = "even";
    var even = true;
    var rows = "";
    for (var i=0; i<uids.length; i++) {
      var _this = uids[i].id || uids[i];
      var unit = this.units[_this];
      rows += '<tr id="row' + _this + '" class="view-row ' + cls + '">';
      rows += this.tmpl.vUnit($, {data: {meta: this.meta,
                                         unit: unit}}).join("");
      rows += '</tr>';
      cls = even ? "odd" : "even";
      even = !even;
    }
    return rows;
  },

  /* Builds context rows for units passed as 'units' */
  buildCtxtRows: function (units) {
    var cls = "even";
    var even = true;
    var rows = "";
    for (var i=0; i<units.length; i++) {
      var unit = units[i];
      rows += '<tr id="ctxt' + unit.id + '" class="context-row ' + cls + '">';
      rows += this.tmpl.vUnit($, {data: {meta: this.meta,
                                         unit: unit}}).join("");
      rows += '</tr>';
      cls = even ? "odd" : "even";
      even = !even;
    }
    return rows;
  },

  /* Gets uids that should be displayed before/after 'uid' */
  getUidsBeforeAfter: function (uid) {
    var uids = {before: [], after: []};
    var limit = parseInt((this.pager.per_page - 1) / 2);
    var current = this.units[uid];
    var prevNext = {prev: "before", next: "after"};
    for (var m in prevNext) {
      var tu = current;
      for (var i=0; i<limit; i++) {
        if (tu[m] != undefined && tu[m] in this.units) {
          var tu = this.units[tu[m]];
          uids[prevNext[m]].push(tu.id);
        }
      }
    }
    if (Object.size(this.units) > limit) {
      var prevNextl = {prev: "after", next: "before"};
      for (var m in prevNext) {
        if (uids[prevNextl[m]].length < limit) {
          // Add (limit - length) units to uids[prevNext[m]]
          var howMuch = limit - uids[prevNextl[m]].length;
          var tu = this.units[uids[prevNext[m]][uids[prevNext[m]].length-1]];
          for (var i=0; i<howMuch; i++) {
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

  /* Sets the edit view for unit 'uid' */
  displayEditUnit: function (uid) {
    if (PTL.editor.hasResults) {
      this.fetchPages(true);
      var uids = this.getUidsBeforeAfter(uid);
      var newTbody = this.buildRows(uids.before) +
                     this.getEditUnit(uid) +
                     this.buildRows(uids.after);
      this.reDraw(newTbody);
    }
  },

  /* reDraws the translate table rows */
  reDraw: function (newTbody) {
    var tTable = $("table.translate-table");
    var where = $("tbody", tTable);
    var oldRows = $("tr", where);
    oldRows.remove();

    // This fixes the issue with tipsy popups staying on the screen
    // if their owner elements have been removed
    $('.tipsy').remove(); // kill all open tipsy popups

    where.append(newTbody);
    $(tTable).trigger("editor_ready");
  },

  /* Fetches more view unit pages in case they're needed */
  fetchPages: function (async) {
    var current = this.currentPage;
    var candidates = [current, current + 1, current - 1];
    var pages = [];

    for (var i=0; i<candidates.length; i++) {
      if (candidates[i] <= this.pager.num_pages &&
          candidates[i] > 0 &&
          !(candidates[i] in this.pagesGot)) {
        pages.push(candidates[i]);
      }
    }
    for (var i=0; i<pages.length; i++) {
      this.getViewUnits(async, pages[i]);
    }
  },

  /* Updates the pager */
  updatePager: function (pager) {
    this.pager = pager;
    // If page number or num_pages has changed, redraw pager
    if (this.currentPage != pager.number
        || this.currentNumPages != pager.num_pages) {
      this.currentPage = pager.number;
      this.currentNumPages = pager.num_pages;
      $("input#item-number").val(pager.number);
      $("span#items-count").text(pager.num_pages);
    }
  },

  /* Loads the edit unit 'uid' */
  getEditUnit: function (uid) {
    var editUrl = l(this.store + '/edit/' + uid);
    var reqData = $.extend({page: this.currentPage}, this.getReqData());
    var widget = '';
    var ctxt = {before: [], after: []};
    $.ajax({
      url: editUrl,
      async: false,
      data: reqData,
      dataType: 'json',
      success: function (data) {
        widget = data['editor'];
        if (data.pager) {
          PTL.editor.updatePager(data.pager);
        }
        if (data.ctxt) {
          PTL.editor.ctxtGap = 2;
          ctxt.before = data.ctxt.before;
          ctxt.after = data.ctxt.after;
        }
      },
      error: PTL.editor.error
    });
    var eclass = "edit-row";
    eclass += this.units[uid].isfuzzy ? " fuzzy-unit" : "";
    // TODO: i18n
    var editor = (ctxt.before.length ? '<tr class="more-context before"><td colspan="2"><a class="morecontext">Show more context rows</a></td></tr>' : '') +
                 this.buildCtxtRows(ctxt.before) +
                 '<tr id="row' + uid + '" class="' + eclass + '">' +
                  widget + '</tr>' +
                  this.buildCtxtRows(ctxt.after) +
                 (ctxt.after.length ? '<tr class="more-context after"><td colspan="2"><a class="morecontext">Show more context rows</a></td></tr>' : '');
    this.activeUid = uid;
    return editor;
  },

  /* Pushes submissions or suggestions and moves to the next unit */
  processSubmit: function (e, type_class) {
    e.preventDefault();
    if (type_class == undefined) {
      type_class = $(e.target).attr("class");
      form_id = "translate";
    } else {
      form_id = "captcha";
    }
    var uid = PTL.editor.activeUid;
    var typeMap = {submit: "submission", suggest: "suggestion"};
    var type = typeMap[type_class];
    var submitUrl = l(PTL.editor.store + '/process/' + uid + '/' + type);
    // Serialize data to be sent
    var reqData = $("form#" + form_id).serialize();
    // TODO: align with the way we're using in other places for getting
    // request data
    reqData += "&page=" + PTL.editor.currentPage + "&filter=" + PTL.editor.filter;
    if (PTL.editor.checks.length) {
      reqData += "&checks=" + PTL.editor.checks.join(",");
    }
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
          if (type == 'submission') {
            PTL.editor.units[uid].isfuzzy = PTL.editor.isFuzzy();
            $("textarea[id^=id_target_f_]").each(function (i) {
              PTL.editor.units[uid].target[i].text = $(this).val();
            });
          }
          var newUid = parseInt(data.new_uid);
          if (newUid) {
            var newHash = "unit/" + newUid;
            $.history.load(newHash);
          }
        }
      },
      error: PTL.editor.error
    });
    return false;
  },

  /* Loads the editor with the next unit */
  gotoPrevNext: function (e) {
    e.preventDefault();
    var current = PTL.editor.units[PTL.editor.activeUid];
    var prevnextMap = {previous: current.prev, next: current.next};
    var newUid = prevnextMap[$(e.target).attr("class")];
    if (newUid != null) {
        var newHash = "unit/" + parseInt(newUid);
        $.history.load(newHash);
    }
  },

  /* Loads the editor with a specific unit */
  gotoUnit: function (e) {
    e.preventDefault();
    if (PTL.editor.getSelectedText() != "") {
      return;
    }
    var m = $(this).attr("id").match(/row([0-9]+)/);
    if (m) {
      var uid = parseInt(m[1]);
      var newHash = "unit/" + uid;
      $.history.load(newHash);
    }
  },

  /* Loads the editor on a specific page */
  gotoPage: function () {
    var page = parseInt($("input#item-number").val());
    if (page && !isNaN(page)) {
      var newHash = "page/" + page;
      $.history.load(newHash);
    }
  },


  /*
   * Units filtering
   */

  /* Gets the failing check options for the current query */
  getCheckOptions: function () {
    var checksUrl = l(this.store + '/checks/');
    var opts;
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
    if (filterBy == "checks") {
      var opts = PTL.editor.getCheckOptions();
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
    } else {
      $("div#filter-checks").remove();
      var newHash = "filter/" + filterBy;
      $.history.load(newHash);
    }
  },

  /* Gets more context units */
  getMoreContext: function () {
    var ctxtUrl = l(PTL.editor.store + '/context/' + PTL.editor.activeUid);
    var reqData = {gap: PTL.editor.ctxtGap};
    $.ajax({
      url: ctxtUrl,
      async: false,
      dataType: 'json',
      data: reqData,
      success: function (data) {
        PTL.editor.ctxtGap += 2;
        var before = PTL.editor.buildCtxtRows(data.ctxt.before);
        var after = PTL.editor.buildCtxtRows(data.ctxt.after);
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
  search: function () {
    // XXX: we can parse search text to allow operators in searches
    // example: "in:source foo"
    var text = $("input#id_search").val();
    if (text) {
      var newHash = "search/" + text;
      $.history.load(newHash);
    }
  },


  /*
   * Suggestions
   */

  fancyEscape: function (text) {
    function replace(match) {
        var replaced,
            escapeHl= '<span class="highlight-escape">%s</span>',
            htmlHl = '<span class="highlight-html">&lt;%s&gt;</span>';
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

  /*
   * Does the actual diffing
   */
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
          // this is part of a substitution, not a plain insertion. We
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
   * Filters TM results and does some processing (add diffs, extra texts, ...)
   */
  filterTMResults: function (results) {
    // FIXME: this just retrieves the first four results
    // we could limit based on a threshold too.
    // FIXME: use localized 'N% match' format string
    var source = $("[id^=id_source_f_]").first().val();
    var filtered = [];
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
    var src = this.meta.source_lang;
    var tgt = this.meta.target_lang;
    var stext = $($("input[id^=id_source_f_]").get(0)).val();
    var tmUrl = this.settings.tmUrl + src + "/" + tgt +
        "/unit/" + encodeURIComponent(stext) + "?jsoncallback=?";
    /* Always abort previous requests so we only get results for the
     * current unit */
    if (this.tmReq != null) {
      this.tmReq.abort();
    }
    this.tmReq = $.jsonp({
      url: tmUrl,
      callback: '_jsonp' + PTL.editor.activeUid,
      dataType: 'jsonp',
      success: function (data) {
        var uid = this.callback.slice(6);
        if (uid == PTL.editor.activeUid && data.length > 0) {
          var filtered = PTL.editor.filterTMResults(data);
          // TODO: i18n
          var name = "amaGama server";
          var tm = PTL.editor.tmpl.tm($, {data: {meta: PTL.editor.meta,
                                                 suggs: filtered,
                                                 name: name}}).join("");
          $("div#suggestion-container").append(tm);
          $("div#amagama_results").animate({height: 'show'}, 1000, 'easeOutQuad');
        }
      },
      error: PTL.editor.error
    });
  },

  /* Rejects a suggestion */
  rejectSuggestion: function () {
    var element = $(this).parent().parent();
    var uid = $('.translate-container input#id_id').val();
    var suggId = $(this).siblings("input.suggid").val();
    var url = l('/suggestion/reject/') + uid + '/' + suggId;
    $.post(url, {'reject': 1},
      function (data) {
        element.fadeOut(200, function () {
          $(this).remove();
          if (!$("div#suggestion-container div[id^=suggestion]").length) {
            $("input.next").trigger("click");
          }
        });
      }, "json");
    return false;
  },

  /* Accepts a suggestion */
  acceptSuggestion: function () {
    var element = $(this).parent().parent();
    var uid = $('.translate-container input#id_id').val();
    var suggId = $(this).siblings("input.suggid").val();
    var url = l('/suggestion/accept/') + uid + '/' + suggId;
    $.post(url, {'accept': 1},
      function (data) {
        $.each(data.newtargets, function (i, target) {
          $("textarea#id_target_f_" + i).val(target).focus();
        });
        $.each(data.newdiffs, function (suggId, sugg) {
          $.each(sugg, function (i, target) {
             $("#suggdiff-" + suggId + "-" + i).html(target);
          });
        });
        $("textarea[id^=id_target_f_]").each(function (i) {
          PTL.editor.units[uid].target[i].text = $(this).val();
        });
        PTL.editor.units[uid].isfuzzy = false;
        element.fadeOut(200, function () {
          $(this).remove();
          if (!$("div#suggestion-container div[id^=suggestion]").length) {
          $("input.next").trigger("click");
          }
        });
      }, "json");
    return false;
  },

  /* Rejects a quality check marking it as false positive */
  rejectCheck: function () {
    var element = $(this).parent();
    var checkId = $(this).siblings("input.checkid").val();
    var uid = $('.translate-container input#id_id').val();
    var url = l('/qualitycheck/reject/') + uid + '/' + checkId;
    $.post(url, {'reject': 1},
      function (data) {
        element.fadeOut(200, function () {
          $(this).remove();
        });
      }, "json");
    return false;
  },


  /*
   * Machine Translation
   */
  isSupportedSource: function (pairs, source) {
    for (var i in pairs) {
      if (source == pairs[i].source) {
        return true;
      }
    }
    return false;
  },

  isSupportedTarget: function (pairs, target) {
    for (var i in pairs) {
      if (target == pairs[i].target) {
        return true;
      }
    }
    return false;
  },

  isSupportedPair: function (pairs, source, target) {
    for (var i in pairs) {
      if (source == pairs[i].source &&
          target == pairs[i].target) {
        return true;
      }
    }
    return false;
  },

  addMTButton: function (aClass, imgFn, tooltip) {
      var btn = '<a class="translate-mt ' + aClass + '">';
      btn += '<img src="' + imgFn + '" title="' + tooltip + '" /></a>';
      $("div.translate-toolbar").first().prepend(btn);
  },

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
    argument_subs[pos] = substring;
    substitute_string = "__" + pos + "__";
    pos = pos + 1;
    return substitute_string;
  },

  escapeHtml: function (s) {
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/\n/,"<br/>");
  }

  };

})(jQuery);
