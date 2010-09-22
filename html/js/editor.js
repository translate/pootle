$(document).ready(function() {

    // Ugly hack to avoid JS templates from being interpreted by Django.
    var stext = $("script[type=text/x-jquery-template]").text();
    stext = stext.replace(/\[\[/g, "{{").replace(/\]\]/g, "}}");
    $("script[type=text/x-jquery-template]").text(stext);

    units = {};

    $(document).ajaxStart(function() {
      $("#activity").show();
    });
    $(document).ajaxStop(function() {
      $("#activity").fadeOut("slow");
    });

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
      // Remove previous rows
      $("tr#row" + uid).prevAll("tr[id]").fadeOut("slow").remove();
      for (var i=0; i<uids.before.length; i++) {
        var _this = uids.before[i];
        var unit = units[_this];
        // Add rows with the newly retrieved data
        var _where = $("<tr></tr>").attr("id", "row" + _this);
        _where.insertBefore(where)
        // FIXME: pass store information as well
        $("#unit_view").tmpl(unit).fadeIn("slow").appendTo(_where);
      }
      // Remove next rows
      $("tr#row" + uid).nextAll("tr[id]").fadeOut("slow").remove();
      for (var i=0; i<uids.after.length; i++) {
        var _this = uids.after[i];
        var unit = units[_this];
        // Add rows with the newly retrieved data
        var _where = $("<tr></tr>").attr("id", "row" + _this);
        _where.insertAfter(where)
        // FIXME: pass store information as well
        $("#unit_view").tmpl(unit).fadeIn("slow").appendTo(_where);
      }
    };

    /*
     * Sets the edit view for unit 'uid'
     */
    var get_edit_unit = function(store, uid) {
      var edit_url = l(store + '/edit/' + uid);
      var where = $("tr#row" + uid);
      where.children().remove();
      where.addClass("translate-translation-row");
      // TODO: Retrieve previous and next units relative to uid
      display_unit_views_for(store, uid);
      where.load(edit_url).hide().fadeIn("slow");
      $("#active_uid").text(uid);
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
        /*var active_uid = $("#active_uid").text();
        display_unit_view(store, active_uid);*/
        get_edit_unit(store, uid);
      }
    });

    $("a[id^=editlink]").ajaxComplete(function() {
      var maxheight = $(window).height() * 0.3;
      $('textarea.expanding').TextAreaExpander('10', maxheight);
      $.scrollTo('td.translate-full', {offset: {top:-100}});
      $(".focusthis").focus();
    });
});
