$(document).ready(function() {

    // TODO: We must namespace all this stuff!!

    // Ugly hack to avoid JS templates from being interpreted by Django.
    $("script[type=text/x-jquery-template]").each(function() {
      var stext = $(this).text();
      stext = stext.replace(/\[\[/g, "{{").replace(/\]\]/g, "}}");
      $(this).text(stext);
    });

    units = {};
    store_info = null;

    $(document).ajaxStart(function() {
      $("#activity").show();
    });
    $(document).ajaxStop(function() {
      $("#activity").fadeOut("slow");
    });

    /*
     * Makes zebra stripes
     */
    function make_zebra(selector) {
      /* Customisation for zebra tags */
      var cls = "even";
      var even = true;
      $(selector).each(function() {
          $(this).addClass(cls)
          cls = even ? "odd" : "even";
          $(this).removeClass(cls)
          even = !even;
      });
    }

    /*
     * Sets the view unit for unit 'uid'
     */
    var get_view_unit = function(store, uid, async) {
      var async = async == undefined ? false : async;
      if (units[uid] == undefined) {
        var view_url = l(store + '/view/' + uid);
        $.ajax({
          url: view_url,
          dataType: 'json',
          async: async,
          success: function(data) {
            if (data.success) {
              units[uid] = data.unit;
            } else {
              // TODO: provide a proper error message and not an alert
              alert("Something went wrong");
              return false;
            }
          }
        });
      }
    };

    var display_unit_view = function(store, uid) {
      get_view_unit(store, uid);
      var unit = units[uid];
      var where = $("tr#row" + uid);
      where.removeClass("translate-translation-row");
      where.children().fadeOut("slow").remove();
      $("#unit_view").tmpl(unit).fadeIn("slow").appendTo(where);
    };

    /*
     * Sets the view units before and after unit 'uid'
     */
    var get_view_units_for = function(store, uid, async, limit) {
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
            update_pager(data.pager);
            if (store_info == null) {
              store_info = data.store;
            }
            $.each(data.units.before, function() {
              units[this.id] = this;
              return_uids.before.push(this.id);
            });
            $.each(data.units.after, function() {
              units[this.id] = this;
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

    var display_unit_views_for = function(store, uid) {
      var uids = get_view_units_for(store, uid);
      var where = $("tr#row" + uid);
      // Remove previous and next rows
      where.prevAll("tr[id]").fadeOut("slow").remove();
      where.nextAll("tr[id]").fadeOut("slow").remove();
      // Add rows with the newly retrieved data
      for (var i=uids.before.length-1; i>=0; i--) {
        var _this = uids.before[i];
        var unit = units[_this];
        var _where = $("<tr></tr>").attr("id", "row" + _this);
        _where.insertBefore(where)
        $("#unit_view").tmpl({store: store_info, unit: unit}).fadeIn("slow").appendTo(_where);
      }
      for (var i=uids.after.length-1; i>=0; i--) {
        var _this = uids.after[i];
        var unit = units[_this];
        var _where = $("<tr></tr>").attr("id", "row" + _this);
        _where.insertAfter(where)
        $("#unit_view").tmpl({store: store_info, unit: unit}).fadeIn("slow").appendTo(_where);
      }
    };

    /*
     * Sets the edit view for unit 'uid'
     */
    var get_edit_unit = function(store, uid) {
      display_unit_views_for(store, uid);
      load_edit_unit(store, uid);
      // TODO: Update pager
      // TODO: make history really load a unit
      window.location.hash = "/u/" + uid;
    };

    $("a[id^=editlink]").live("click", function(e) {
      e.preventDefault();
      var m = $(this).attr("id").match(/editlink([0-9]+)/);
      if (m) {
        var uid = m[1];
        var store = $("div#store").text();
        get_edit_unit(store, uid);
      }
    });

    /*
     * Stuff to be done when the editor is ready.
     */
    $("table.translate-table").bind("editor_ready", function() {
      make_zebra("table.translate-table tr[id]");
      var maxheight = $(window).height() * 0.3;
      $('textarea.expanding').TextAreaExpander('10', maxheight);
      $(".focusthis").focus();
    });

    var update_pager = function(pager) {
      if (pager) {
        var newpager = $("#pager").tmpl({pager: pager}).get(0);
        $("div.translation-nav").children().remove();
        $("div.translation-nav").append(newpager);
      }
    };

    var load_edit_unit = function(store, uid) {
      var edit_url = l(store + '/edit/' + uid);
      var edit_where = $("tr#row" + uid);
      edit_where.children().remove();
      edit_where.addClass("translate-translation-row");
      edit_where.load(edit_url, function() {
        $("table.translate-table").trigger("editor_ready");
      });
      $("#active_uid").text(uid);
    };

    var display_next_unit = function(store, data) {
      update_pager(data.pager);
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
      $("#unit_view").tmpl({store: data.store, unit: data.prev_unit}).fadeIn("slow").appendTo(prev_where);
      // Last unit
      if (data.last_unit) {
        var last_in_table = $("table.translate-table tr[id]").last();
        var last_where = $("<tr></tr>").attr("id", "row" + data.last_unit.id);
        last_where.insertAfter(last_in_table)
        $("#unit_view").tmpl({store: data.store, unit: data.last_unit}).fadeIn("slow").appendTo(last_where);
      }
      // Editing unit
      if (data.new_uid) {
        load_edit_unit(store, data.new_uid);
        // TODO: make history really load a unit
        window.location.hash = "/u/" + data.new_uid;
      }
    };

    var process_submit = function(store, uid, type) {
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
            display_next_unit(store, data);
          } else {
            // TODO: provide a proper error message and not an alert
            alert("Something went wrong");
            return false;
          }
        }
      });
    };

    $("input.submit").live("click", function(e) {
      e.preventDefault();
      var store = $("div#store").text();
      var current_unit = $("#active_uid").text();
      process_submit(store, current_unit, 'submission');
    });

    $("input.suggest").live("click", function(e) {
      e.preventDefault();
      var store = $("div#store").text();
      var current_unit = $("#active_uid").text();
      process_submit(store, current_unit, 'suggestion');
    });
});
