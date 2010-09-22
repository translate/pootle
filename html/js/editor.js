(function($) {
  /* Define namespaces */
  // XXX: Should we define the global pootle namespace somewhere else?
  if (!window.pootle) { window.pootle = {}; }
  if (!pootle.editor) { pootle.editor = {}; }

  pootle.editor.units = {};
  pootle.editor.store_info = null;

  /*
   * Initializes the editor
   */
  pootle.editor.init = function() {
    /* Ugly hack to avoid JS templates from being interpreted by Django. */
    $("script[type=text/x-jquery-template]").each(function() {
      var stext = $(this).text();
      stext = stext.replace(/\[\[/g, "{{").replace(/\]\]/g, "}}");
      $(this).text(stext);
    });

    /*
     * XHR activity indicator
     */
    $(document).ajaxStart(function() {
      $("#activity").show();
    });
    $(document).ajaxStop(function() {
      $("#activity").fadeOut("slow");
    });

    /* History support */
    $.history.init(function(hash) {
      var parts = hash.split("/");
      switch (parts[0]) {
        case "unit":
          var store = $("div#store").text();
          var uid = parts[1];
         pootle.editor.display_edit_unit(store, uid);
        break;
      }
    }, {'unescape': true});

    /* Check first when loading the page */
    $.history.check();
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
   * Sets the view unit for unit 'uid'
   * XXX: Really used? *
   */
  pootle.editor.get_view_unit = function(store, uid, async) {
    var async = async == undefined ? false : async;
    if (pootle.editor.units[uid] == undefined) {
      var view_url = l(store + '/view/' + uid);
      $.ajax({
        url: view_url,
        dataType: 'json',
        async: async,
        success: function(data) {
          if (data.success) {
            pootle.editor.units[uid] = data.unit;
          } else {
            // TODO: provide a proper error message and not an alert
            alert("Something went wrong");
            return false;
          }
        }
      });
    }
  };

  /* XXX: Really used? */
  pootle.editor.display_unit_view = function(store, uid) {
    pootle.editor.get_view_unit(store, uid);
    var unit = pootle.editor.units[uid];
    var where = $("tr#row" + uid);
    where.removeClass("translate-translation-row");
    where.children().fadeOut("slow").remove();
    $("#unit_view").tmpl(unit).appendTo(where);
  };

  /*
   * Sets the view units before and after unit 'uid'
   */
  pootle.editor.get_view_units_for = function(store, uid, async, limit) {
    var async = async == undefined ? false : async;
    var limit = limit == undefined ? 0: limit;
    var url_str = store + '/view/for/' + uid;
    url_str = limit ? url_str + 'limit/' + limit : url_str;
    var view_for_url = l(url_str);
    var return_uids = {before: [], after: []};
    $.ajax({
      url: view_for_url,
      dataType: 'json',
      async: async,
      success: function(data) {
        if (data.success) {
          // XXX: is this the right place for updating the pager?
          pootle.editor.update_pager(data.pager);
          if (pootle.editor.store_info == null) {
            pootle.editor.store_info = data.store;
          }
          $.each(data.units.before, function() {
            pootle.editor.units[this.id] = this;
            return_uids.before.push(this.id);
          });
          $.each(data.units.after, function() {
            pootle.editor.units[this.id] = this;
            return_uids.after.push(this.id);
          });
        } else {
          // TODO: provide a proper error message and not an alert
          alert("Something went wrong");
          return false;
        }
      }
    });
    return return_uids;
  };

  pootle.editor.display_unit_views_for = function(store, uid) {
    var uids = pootle.editor.get_view_units_for(store, uid);
    // FIXME: This only works for visible units:
    // -- what happens if we want to load a unit which is out of context?
    var where = $("tr#row" + uid);
    // Remove previous and next rows
    where.prevAll("tr[id]").fadeOut("slow").remove();
    where.nextAll("tr[id]").fadeOut("slow").remove();
    // Add rows with the newly retrieved data
    for (var i=uids.before.length-1; i>=0; i--) {
      var _this = uids.before[i];
      var unit = pootle.editor.units[_this];
      var _where = $("<tr></tr>").attr("id", "row" + _this);
      _where.insertBefore(where)
      $("#unit_view").tmpl({store: pootle.editor.store_info, unit: unit}).appendTo(_where);
    }
    for (var i=uids.after.length-1; i>=0; i--) {
      var _this = uids.after[i];
      var unit = pootle.editor.units[_this];
      var _where = $("<tr></tr>").attr("id", "row" + _this);
      _where.insertAfter(where)
      $("#unit_view").tmpl({store: pootle.editor.store_info, unit: unit}).appendTo(_where);
    }
  };

  /*
   * Sets the edit view for unit 'uid'
   */
  pootle.editor.display_edit_unit = function(store, uid) {
    pootle.editor.display_unit_views_for(store, uid);
    pootle.editor.load_edit_unit(store, uid);
  };

  /*
   * Updates the pager
   */
  pootle.editor.update_pager = function(pager) {
    if (pager) {
      var newpager = $("#pager").tmpl({pager: pager}).get(0);
      $("div.translation-nav").children().remove();
      $("div.translation-nav").append(newpager);
    }
  };

  /*
   * Loads the edit unit uid.
   */
  pootle.editor.load_edit_unit = function(store, uid) {
    var edit_url = l(store + '/edit/' + uid);
    var edit_where = $("tr#row" + uid);
    edit_where.children().remove();
    edit_where.addClass("translate-translation-row");
    edit_where.load(edit_url, function() {
      $("table.translate-table").trigger("pootle.editor.ready");
    });
    $("#active_uid").text(uid);
  };

  /*
   * Displays the next edit unit
   */
  pootle.editor.display_next_unit = function(store, data) {
    pootle.editor.update_pager(data.pager);
    var prev_where = $("tr#row" + data.prev_unit.id);
    // Only remove first unit in the table if it's not the editing widget
    var first_in_table = $("table.translate-table tr[id]").first();
    if (prev_where.get(0) != first_in_table.get(0)) {
      // FIXME: We don't have to do this until the edit unit
      // is on the center
      $(first_in_table).remove();
    }
    // Previous unit
    var prev_where = $("tr#row" + data.prev_unit.id);
    prev_where.removeClass("translate-translation-row");
    prev_where.children().fadeOut("slow").remove();
    $("#unit_view").tmpl({store: data.store, unit: data.prev_unit}).appendTo(prev_where);
    // Last unit
    if (data.last_unit) {
      var last_in_table = $("table.translate-table tr[id]").last();
      var last_where = $("<tr></tr>").attr("id", "row" + data.last_unit.id);
      last_where.insertAfter(last_in_table)
      $("#unit_view").tmpl({store: data.store, unit: data.last_unit}).appendTo(last_where);
    }
    // Editing unit
    if (data.new_uid) {
      pootle.editor.load_edit_unit(store, data.new_uid);
    }
  };

  /*
   * Pushes submissions or suggestions and moves to the next unit
   */
  pootle.editor.process_submit = function(e) {
    e.preventDefault();
    var store = $("div#store").text();
    var uid = $("#active_uid").text();
    var type_map = {submit: "submission", suggest: "suggestion"};
    var type = type_map[$(e.target).attr("class")];
    var submit_url = l(store + '/process/' + uid + '/' + type);
    // Serialize data to be sent
    var post_data = $("form#translate").serialize();
    $.ajax({
      url: submit_url,
      type: 'POST',
      data: post_data,
      dataType: 'json',
      async: false,
      success: function(data) {
        if (data.success) {
          pootle.editor.display_next_unit(store, data);
        } else {
          // TODO: provide a proper error message and not an alert
          alert("Something went wrong");
          return false;
        }
      }
    });
    return false;
  };

  /*
   * Loads the editor with the next unit
   */
  pootle.editor.goto_prevnext = function(e) {
    e.preventDefault();
    var current = $("tr#row" + $("#active_uid").text());
    var prevnext_map = {previous: current.prev("tr[id]"), next: current.next("tr[id]")};
    var prevnext = prevnext_map[$(e.target).attr("class")];
    if (prevnext.length) {
      var m = prevnext.attr("id").match(/row([0-9]+)/);
      if (m) {
        var uid = m[1];
        var newhash = "unit/" + uid;
        $.history.load(newhash);
      }
    }
  };

  /*
   * Loads the editor with a specific unit
   */
  pootle.editor.goto_unit = function(e) {
    e.preventDefault();
    var m = $(this).attr("id").match(/editlink([0-9]+)/);
    if (m) {
      var uid = m[1];
      var newhash = "unit/" + uid;
      $.history.load(newhash);
    }
  };

  /* Bind event handlers */
  $("table.translate-table").live("pootle.editor.ready", pootle.editor.ready);
  $("a[id^=editlink]").live("click", pootle.editor.goto_unit);
  $("input.submit, input.suggest").live("click", pootle.editor.process_submit);
  $("input.previous, input.next").live("click", pootle.editor.goto_prevnext);

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

})(jQuery);

$(document).ready(function() {
  pootle.editor.init();
});
