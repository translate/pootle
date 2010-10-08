(function($) {
  /* Define namespaces */
  // XXX: Should we define the global pootle namespace somewhere else?
  if (!window.pootle) { window.pootle = {}; }
  if (!pootle.editor) { pootle.editor = {}; }

  /*
   * Initializes the editor
   */
  pootle.editor.init = function() {

    pootle.editor.units = {};
    pootle.editor.store = $("div#store").text();
    pootle.editor.active_uid = $("#active_uid").text();
    pootle.editor.pages_got = {};

    /* Ugly hack to avoid JS templates from being interpreted by Django. */
    $("script[type=text/x-jquery-template]").each(function() {
      var stext = $(this).text();
      stext = stext.replace(/\[\[/g, "{{").replace(/\]\]/g, "}}");
      $(this).text(stext);
    });

    /* Set initial focus on page load */
    pootle.editor.focused = $(".translate-original-focus textarea").get(0);
    if (pootle.editor.focused != null) {
        pootle.editor.focused.focus();
    }

    /* Update focus when appropriate */
    $(".focusthis").live("focus", function(e) {
      pootle.editor.focused = e.target;
    });

    /* Write TM results into the currently focused element */
    // TODO: refactor write TM and writespecial within a single function
    $(".writetm").live("click", function() {
      var tmtext = $(".tm-translation", this).text();
      var element = $(pootle.editor.focused);
      var start = element.caret().start + tmtext.length;
      element.val(element.caret().replace(tmtext));
      element.caret(start, start);
    });

    /* Write special chars, tags and escapes into the currently focused element */
    $(".writespecial, .translate-full .translation-highlight-escape, .translate-full .translation-highlight-html").live("click", function() {
      var specialtext = $(this).text();
      var element = $(pootle.editor.focused);
      var start = element.caret().start + specialtext.length;
      element.val(element.caret().replace(specialtext));
      element.caret(start, start);
    });

    /* Copy original translation */
    $("a.copyoriginal").live("click", function() {
      var sources = $(".translation-text", $(this).parent().parent().parent());
      var clean_sources = [];
      $.each(sources, function(i) {
        clean_sources[i] = $(this).text()
                                  .replace("\n", "\\n\n", "g")
                                  .replace("\t", "\\t", "g");
      });

      var targets = $("[id^=id_target_f_]");
      if (targets.length) {
        var max = clean_sources.length - 1;
        for (var i=0; i<targets.length; i++) {
          var newval = clean_sources[i] || clean_sources[max];
          $(targets.get(i)).val(newval);
        }
        $(targets).get(0).focus();
        pootle.editor.goFuzzy();
      }
    });

    /* Fuzzy / unfuzzy */
    pootle.editor.keepstate = false;
    $("textarea.translation").live("keyup blur", function() {
      if (!pootle.editor.keepstate && $(this).attr("defaultValue") != $(this).val()) {
        pootle.editor.ungoFuzzy();
      }
    });

    $("input.fuzzycheck").live("click", function() {
      if (pootle.editor.isFuzzy()) {
        pootle.editor.doFuzzyArea();
      } else {
        pootle.editor.undoFuzzyArea();
      }
    });

    /* Collapsing */
    $(".collapse").live("click", function(event) {
      event.preventDefault();
      $(this).siblings(".collapsethis").slideToggle("fast");
      if ($("textarea", $(this).next("div.collapsethis")).length) {
        $("textarea", $(this).next("div.collapsethis")).focus();
      }
    });

    /* Bind event handlers */
    $("table.translate-table").live("pootle.editor.ready", pootle.editor.ready);
    $("a[id^=editlink]").live("click", pootle.editor.goto_unit);
    $("input.submit, input.suggest").live("click", pootle.editor.process_submit);
    $("input.previous, input.next").live("click", pootle.editor.goto_prevnext);
    $("#translate-suggestion-container .rejectsugg").live("click", pootle.editor.reject_suggestion);
    $("#translate-suggestion-container .acceptsugg").live("click", pootle.editor.accept_suggestion);
    $("#translate-checks-block .rejectcheck").live("click", pootle.editor.reject_check);

    /* Bind hotkeys */
    shortcut.add('ctrl+return', function() {
      $("input.submit").trigger("click");
    });
    shortcut.add('ctrl+shift+return', function() {
      $("input.suggest").trigger("click");
    });
    shortcut.add('ctrl+up', function() {
      $("input.previous").trigger("click");
    });
    shortcut.add('ctrl+down', function() {
      $("input.next").trigger("click");
    });

    /* XHR activity indicator */
    $(document).ajaxStart(function() {
      $("#xhr-error").hide();
      $("#xhr-activity").show();
    });
    $(document).ajaxStop(function() {
      $("#xhr-activity").hide();
    });

    /* Retrieve metadata used for this query */
    pootle.editor.get_meta();

    /* History support */
    $.history.init(function(hash) {
      var parts = hash.split("/");
      switch (parts[0]) {
        case "unit":
          var uid = parseInt(parts[1]);
          // Take care when we want to access a unit directly from a permalink
          if (pootle.editor.active_uid != uid
              && pootle.editor.units[uid] == undefined) {
            pootle.editor.active_uid = uid;
            pootle.editor.get_meta();
          }
          pootle.editor.display_edit_unit(pootle.editor.store, uid);
        break;
      }
    }, {'unescape': true});
  };

  /*
   * Stuff to be done when the editor is ready
   */
  pootle.editor.ready = function() {
    pootle.editor.make_zebra("table.translate-table tr[id]");
    var maxheight = $(window).height() * 0.3;
    $('textarea.expanding').TextAreaExpander('10', maxheight);
    $(".focusthis").focus();
  }

  /*
   * Makes zebra stripes
   * XXX: move this over pootle.util ?
   */
  pootle.editor.make_zebra = function(selector) {
    /* Customisation for zebra tags */
    var cls = "even";
    var even = true;
    $(selector).each(function() {
      $(this).addClass(cls)
      cls = even ? "odd" : "even";
      $(this).removeClass(cls)
      even = !even;
    });
  };

  /*
   * Fuzzying / unfuzzying functions
   */
  pootle.editor.doFuzzyArea = function() {
    $("tr.translate-translation-row").addClass("translate-translation-fuzzy");
  };

  pootle.editor.undoFuzzyArea = function() {
    $("tr.translate-translation-row").removeClass("translate-translation-fuzzy");
  };

  pootle.editor.doFuzzyBox = function() {
    var checkbox = $("input.fuzzycheck");
    if (!pootle.editor.isFuzzy()) {
      checkbox.attr("checked", "checked");
    }
  };

  pootle.editor.undoFuzzyBox = function() {
    var checkbox = $("input.fuzzycheck");
    if (pootle.editor.isFuzzy()) {
      checkbox.removeAttr("checked");
    }
  };

  pootle.editor.goFuzzy = function() {
    if (!pootle.editor.isFuzzy()) {
      pootle.editor.keepstate = true;
      pootle.editor.doFuzzyArea();
      pootle.editor.doFuzzyBox();
    }
  };

  pootle.editor.ungoFuzzy = function() {
    if (pootle.editor.isFuzzy()) {
      pootle.editor.keepstate = true;
      pootle.editor.undoFuzzyArea();
      pootle.editor.undoFuzzyBox();
    }
  };

  pootle.editor.isFuzzy = function() {
    var checkbox = $("input.fuzzycheck");
    var checked = checkbox.attr("checked");
    if (checked == undefined || checked == false) {
      return false;
    } else {
      return true;
    }
  };

  /*
   * Displays error messages returned in XHR requests
   */
  pootle.editor.error = function(msg) {
    if (msg) {
      $("#xhr-activity").hide();
      $("#xhr-error span").text(msg).parent().show();
    }
  };


  /*
   * Unit navigation, display, submission
   */

  /* Retrieves the metadata used for this query */
  pootle.editor.get_meta = function() {
    var meta_url = l(pootle.editor.store + "/meta/" + pootle.editor.active_uid);
    $.ajax({
      url: meta_url,
      async: false,
      dataType: 'json',
      success: function(data) {
        pootle.editor.meta = data.meta;
        pootle.editor.update_pager(data.pager);
        pootle.editor.current_page = data.pager.number;
        pootle.editor.check_pages(false);
      },
    });
  };

  /* Gets the view units that refer to current_page */
  pootle.editor.get_view_units = function(store, async, page, limit) {
    var async = async == undefined ? false : async;
    var page = page == undefined ? pootle.editor.current_page : page;
    var limit = limit == undefined ? 0 : limit;
    var url_str = store + '/view';
    url_str = limit ? url_str + '/limit/' + limit : url_str;
    var view_for_url = l(url_str);
    $.ajax({
      url: view_for_url,
      data: {'page': page},
      dataType: 'json',
      async: async,
      success: function(data) {
        if (data.success) {
          pootle.editor.pages_got[page] = [];
          $.each(data.units, function() {
            pootle.editor.units[this.id] = this;
            pootle.editor.pages_got[page].push(this.id);
          });
        } else {
          pootle.editor.error(data.msg);
        }
      }
    });
  };

  /* Builds view rows for units represented by 'uids' */
  pootle.editor.build_rows = function(uids) {
    var rows = "";
    for (var i=0; i<uids.length; i++) {
      var _this = uids[i].id || uids[i];
      var unit = pootle.editor.units[_this];
      var viewunit = $('<tbody><tr id="row' + _this + '"></tr></tbody>');
      var row = $('tr', viewunit);
      $("#unit_view").tmpl({meta: pootle.editor.meta,
                            unit: unit}).appendTo(row);
      rows += viewunit.html();
    }
    return rows;
  };

  /* Gets uids that should be displayed before/after 'uid' */
  pootle.editor.get_uids_before_after = function(uid) {
    var uids = {before: [], after: []};
    var limit = (pootle.editor.pager.per_page - 1) / 2;
    var current = pootle.editor.units[uid];
    var prevnext = {prev: "before", next: "after"};
    for (m in prevnext) {
      var tu = current;
      for (var i=0; i<limit; i++) {
        if (tu[m] != undefined) {
          var tu = pootle.editor.units[tu[m]];
          uids[prevnext[m]].push(tu.id);
        }
      }
    }
    var prevnextl = {prev: "after", next: "before"};
    for (m in prevnext) {
      if (uids[prevnextl[m]].length < limit) {
        // Add (limit - lenght) units to uids[prevnext[m]]
        var how_much = limit - uids[prevnextl[m]].length;
        var tu = pootle.editor.units[uids[prevnext[m]][uids[prevnext[m]].length-1]];
        for (var i=0; i<how_much; i++) {
          if (tu[m] != undefined) {
            var tu = pootle.editor.units[tu[m]];
            uids[prevnext[m]].push(tu.id);
          }
        }
      }
    }
    uids.before.reverse();
    return uids;
  };

  /* Sets the edit view for unit 'uid' */
  pootle.editor.display_edit_unit = function(store, uid) {
    // TODO: Try to add stripe classes on the fly, not at a separate
    // time after rendering
    pootle.editor.check_pages(true);
    var uids = pootle.editor.get_uids_before_after(uid);
    var newtbody = pootle.editor.build_rows(uids.before) +
                   pootle.editor.get_edit_unit(store, uid) +
                   pootle.editor.build_rows(uids.after);
    pootle.editor.redraw(newtbody);
  };

  /* Redraws the translate table rows */
  pootle.editor.redraw = function(newtbody) {
    var ttable = $("table.translate-table");
    var where = $("tbody", ttable);
    var oldrows = $("tr", where);
    oldrows.remove();
    where.append(newtbody);
    $(ttable).trigger("pootle.editor.ready");
  };

  /* Checks if the editor needs to retrieve more view unit pages */
  pootle.editor.check_pages = function(async) {
    var current = pootle.editor.current_page;
    var candidates = [current, current + 1, current - 1];
    var pages = [];

    for (var i=0; i<candidates.length; i++) {
      if (candidates[i] <= pootle.editor.pager.num_pages &&
          candidates[i] > 0 &&
          !(candidates[i] in pootle.editor.pages_got)) {
        pages.push(candidates[i]);
      }
    }
    for (var i=0; i<pages.length; i++) {
      pootle.editor.get_view_units(pootle.editor.store, async, pages[i]);
    }
  };

  /* Updates the pager */
  pootle.editor.update_pager = function(pager) {
    pootle.editor.pager = pager;
    // If page number has changed, redraw pager
    if (pootle.editor.current_page != pager.number) {
      pootle.editor.current_page = pager.number;
      var newpager = $("#pager").tmpl({pager: pager}).get(0);
      $("div.translation-nav").children().remove();
      $("div.translation-nav").append(newpager);
    }
  };

  /* Loads the edit unit 'uid' */
  pootle.editor.get_edit_unit = function(store, uid) {
    var edit_url = l(store + '/edit/' + uid);
    var editor = '<tr id="row' + uid + '" class="translate-translation-row">';
    var widget = '';
    $.ajax({
      url: edit_url,
      async: false,
      data: {page: pootle.editor.current_page},
      dataType: 'json',
      success: function(data) {
        widget = data['editor'];
        if (data.pager) {
          pootle.editor.update_pager(data.pager);
        }
      },
    });
    editor += widget + '</tr>';
    pootle.editor.active_uid = uid;
    return editor;
  };

  /* Pushes submissions or suggestions and moves to the next unit */
  pootle.editor.process_submit = function(e, type_class) {
    e.preventDefault();
    if (type_class == undefined) {
      type_class = $(e.target).attr("class");
      form_id = "translate";
    } else {
      form_id = "captcha";
    }
    var uid = pootle.editor.active_uid;
    var type_map = {submit: "submission", suggest: "suggestion"};
    var type = type_map[type_class];
    var submit_url = l(pootle.editor.store + '/process/' + uid + '/' + type);
    // Serialize data to be sent
    var post_data = $("form#" + form_id).serialize();
    post_data += "&page=" + pootle.editor.current_page;
    $.ajax({
      url: submit_url,
      type: 'POST',
      data: post_data,
      dataType: 'json',
      async: false,
      success: function(data) {
        if (data.captcha) {
          $.fancybox(data.captcha);
          $("input#id_captcha_answer").focus();
        } else {
          if (data.success) {
            if (type == 'submission') {
              $("textarea[id^=id_target_f_]").each(function(i) {
                pootle.editor.units[uid].target[i].text = $(this).val();
              });
            }
            var newhash = "unit/" + parseInt(data.new_uid);
            $.history.load(newhash);
          } else {
            pootle.editor.error(data.msg);
          }
        }
      }
    });
    return false;
  };

  /* Loads the editor with the next unit */
  pootle.editor.goto_prevnext = function(e) {
    e.preventDefault();
    var current = pootle.editor.units[pootle.editor.active_uid];
    var prevnext_map = {previous: current.prev, next: current.next};
    var new_uid = prevnext_map[$(e.target).attr("class")];
    if (new_uid != null) {
        var newhash = "unit/" + parseInt(new_uid);
        $.history.load(newhash);
    }
  };

  /* Loads the editor with a specific unit */
  pootle.editor.goto_unit = function(e) {
    e.preventDefault();
    var m = $(this).attr("id").match(/editlink([0-9]+)/);
    if (m) {
      var uid = m[1];
      var newhash = "unit/" + parseInt(uid);
      $.history.load(newhash);
    }
  };


  /*
   * Suggestions handling
   */

  /* Rejects a suggestion */
  pootle.editor.reject_suggestion = function() {
    var element = $(this).parent().parent();
    var uid = $('.translate-container input#id_id').val();
    var suggid = $(this).siblings("input.suggid").val();
    var url = l('/suggestion/reject/') + uid + '/' + suggid;
    $.post(url, {'reject': 1},
           function(rdata) {
             element.fadeOut(200, function() {
               $(this).remove();
               if (!$("div#translate-suggestion-container div.translate-suggestion").length) {
                 $("input.next").trigger("click");
               }
             });
           }, "json");
    return false;
  };

  /* Accepts a suggestion */
  pootle.editor.accept_suggestion = function() {
    var element = $(this).parent().parent();
    var uid = $('.translate-container input#id_id').val();
    var suggid = $(this).siblings("input.suggid").val();
    var url = l('/suggestion/accept/') + uid + '/' + suggid;
    $.post(url, {'accept': 1},
           function(rdata) {
             $.each(rdata.newtargets, function(i, target) {
               $("textarea#id_target_f_" + i).val(target).focus();
             });
             $.each(rdata.newdiffs, function(suggid, sugg) {
               $.each(sugg, function(i, target) {
                 $("#suggdiff-" + suggid + "-" + i).html(target);
               });
             });
             $("textarea[id^=id_target_f_]").each(function(i) {
               pootle.editor.units[uid].target[i].text = $(this).val();
             });
             element.fadeOut(200, function() {
               $(this).remove();
               if (!$("div#translate-suggestion-container div.translate-suggestion").length) {
                 $("input.next").trigger("click");
               }
             });
           }, "json");
    return false;
  };

  /* Rejects a quality check marking it as false positive */
  pootle.editor.reject_check = function() {
    var element = $(this).parent();
    var checkid = $(this).siblings("input.checkid").val();
    var uid = $('.translate-container input#id_id').val();
    var url = l('/qualitycheck/reject/') + uid + '/' + checkid;
    $.post(url, {'reject': 1},
           function(rdata) {
             element.fadeOut(200, function() {
               $(this).remove();
             });
           }, "json");
    return false;
  };


  /*
   * Machine Translation
   */
  pootle.editor.isSupportedSource = function(pairs, source) {
    for (var i in pairs) {
      if (source == pairs[i].source) {
        return true;
      }
    }
    return false;
  };

  pootle.editor.isSupportedTarget = function(pairs, target) {
    for (var i in pairs) {
      if (target == pairs[i].target) {
        return true;
      }
    }
    return false;
  };

  pootle.editor.isSupportedPair = function(pairs, source, target) {
    for (var i in pairs) {
      if (source == pairs[i].source &&
          target == pairs[i].target) {
        return true;
      }
    }
    return false;
  };

  pootle.editor.addMTButton = function(element, aclass, imgfn, tooltip) {
      var a = document.createElement("a");
      a.setAttribute("class", "translate-mt " + aclass);
      var img = document.createElement("img");
      img.setAttribute("src", imgfn);
      img.setAttribute("title", tooltip);
      a.appendChild(img);
      element.prepend(a);
  };

  pootle.editor.normalize_code = function(locale) {
      var clean = locale.replace('_', '-')
      var atIndex = locale.indexOf("@");
      if (atIndex != -1) {
        clean = clean.slice(0, atIndex);
      }
      return clean;
  };

  pootle.editor.collectArguments = function(substring) {
    if (substring == '%%') {
      return '%%';
    }
    argument_subs[pos] = substring;
    substitute_string = "__" + pos + "__";
    pos = pos + 1;
    return substitute_string;
  };

})(jQuery);
