$(document).ready(function() {

    var units = new Array();

    /*
     * Sets the unit view for unit 'uid'
     */
    var get_unit_view = function(store, uid) {
      if (units[uid] == undefined) {
        var view_url = l(store + '/unit/view/' + uid);
        $.getJSON(view_url, function(data) {
          if (data.success) {
            units[uid] = data.unit;
          } else {
            // TODO: provide a proper error message and not an alert
            alert("Something went wrong");
            return false;
          }
        });
      }
    };

    var display_unit_view = function(uid) {
      var unit = units[uid];
      var where = $("tr#row" + uid);
      where.children().remove();
      $("#unit_view").tmpl(unit).appendTo(where);
    };

    /*
     * Sets the edit view for unit 'uid'
     */
    var get_unit_edit = function(store, uid) {
      var edit_url = l(store + '/unit/edit/' + uid);
      var where = $("tr#row" + uid);
      where.children().remove();
      where.load(edit_url);
      $("#active_uid").text(uid);
    };

    /*
     * Restores the current edit unit into a view unit.
     */
    var restore_active_unit = function(store, uid) {
      get_unit_view(store, uid);
      display_unit_view(uid);
    };

    $("a[id^=editlink]").live("click", function(e) {
      e.preventDefault();
      if (!$(this).parent().next("td").hasClass("translate-full")) {
        // Retrieve unit i+1, if any
        var m = $(this).attr("id").match(/editlink([0-9]+)/);
        if (m) {
          var uid = m[1];
          var store = $("div#store").text();
          var active_uid = $("#active_uid").text();
          restore_active_unit(store, active_uid);
          get_unit_edit(store, uid);
        }
      }
    });
});
