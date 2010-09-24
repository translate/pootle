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
      $("#xhr-error").hide();
      $("#xhr-activity").show();
    });
    $(document).ajaxStop(function() {
      $("#xhr-activity").fadeOut("slow");
    });

    /* History support */
    $.history.init(function(hash) {
      var parts = hash.split("/");
      switch (parts[0]) {
        case "unit":
          var store = $("div#store").text();
          var uid = parseInt(parts[1]);
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
   * Displays error messages returned in XHR requests
   */
  pootle.editor.error = function(msg) {
    if (msg) {
      $("#xhr-activity").hide();
      $("#xhr-error span").text(msg).parent().show();
    }
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
          pootle.editor.error(data.msg);
        }
        return_uids.success = data.success;
      }
    });
    return return_uids;
  };

  pootle.editor.build_rows = function(uids) {
    var rows = "";
    for (var i=uids.length-1; i>=0; i--) {
      var _this = uids[i].id || uids[i];
      var unit = pootle.editor.units[_this];
      var viewunit = $('<tbody><tr id="row' + _this + '"></tr></tbody>');
      var row = $('tr', viewunit);
      $("#unit_view").tmpl({store: pootle.editor.store_info,
                            unit: unit}).appendTo(row);
      rows += viewunit.html();
    }
    return rows;
  };

  /*
   * Sets the edit view for unit 'uid'
   */
  pootle.editor.display_edit_unit = function(store, uid) {
    // TODO: Try to add stripe classes on the fly, not at a separate
    // time after rendering
    var uids = pootle.editor.get_view_units_for(store, uid);
    if (uids.success) {
      var newtbody = pootle.editor.build_rows(uids.before) +
                     pootle.editor.get_edit_unit(store, uid) +
                     pootle.editor.build_rows(uids.after);
      pootle.editor.redraw(newtbody);
    }
  };

  /*
   * Redraws the translate table rows
   */
  pootle.editor.redraw = function(newtbody) {
    var ttable = $("table.translate-table");
    var where = $("tbody", ttable);
    var oldrows = $("tr", where);
    oldrows.remove();
    where.append(newtbody);
    $(ttable).trigger("pootle.editor.ready");
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
  pootle.editor.get_edit_unit = function(store, uid) {
    var edit_url = l(store + '/edit/' + uid);
    var editor = '<tr id="row' + uid + '" class="translate-translation-row">';
    var widget = '';
    $.ajax({
      url: edit_url,
      async: false,
      success: function(data) {
        widget = data;
      },
    });
    editor += widget + '</tr>';
    $("#active_uid").text(uid);
    return editor;
  };

  /*
   * Displays the next edit unit
   */
  pootle.editor.display_next_unit = function(store, data) {
    pootle.editor.update_pager(data.pager);
    var newtbody = pootle.editor.build_rows(data.units.before);
    if (data.new_uid) {
      newtbody += pootle.editor.get_edit_unit(store, data.new_uid);
    }
    newtbody += pootle.editor.build_rows(data.units.after);
    pootle.editor.redraw(newtbody);
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
          // Update client data
          if (pootle.editor.store_info == null) {
            pootle.editor.store_info = data.store;
          }
          $.each(data.units.before, function() {
            pootle.editor.units[this.id] = this;
          });
          $.each(data.units.after, function() {
            pootle.editor.units[this.id] = this;
          });
          pootle.editor.display_next_unit(store, data);
        } else {
          pootle.editor.error(data.msg);
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
