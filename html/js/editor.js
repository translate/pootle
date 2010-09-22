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
            display_unit_view(uid);
          } else {
            // TODO: provide a proper error message and not an alert
            alert("Something went wrong");
            return false;
          }
        });
      } else {
        display_unit_view(uid);
      }
    };

    var display_unit_view = function(uid) {
      var unit = units[uid];
      var where = $("a#editlink" + uid).parent();
      where.siblings().remove();
      var source = '<td class="translate-original">',
          target = '<td class="translate-translation">';
      $(unit.source).each(function() {
        source += '<div class="translation-text">' + this + '</div>';
      });
      source += '</td>';
      $(unit.target).each(function() {
        target += '<div class="translation-text">' + this + '</div>';
      });
      target += '</td>';
      where.parent().append(source);
      where.parent().append(target);
    };

    /*
     * Sets the edit view for unit 'uid'
     */
    var get_unit_edit = function(store, uid) {
      var edit_url = l(store + '/unit/edit/' + uid);
      var where = $("a#editlink" + uid).closest("tr");
      where.children().remove();
      where.load(edit_url);
    };

    /*
     * Restores the current edit unit into a view unit.
     */
    var restore_active_unit = function(store, uid) {
      get_unit_view(store, uid);
    };

    $("a[id^=editlink]").click(function(e) {
      e.preventDefault();
      if (!$(this).parent().next("td").hasClass("translate-full")) {
        // Retrieve unit i+1, if any
        var m = $(this).attr("id").match(/editlink([0-9]+)/);
        if (m) {
          var uid = m[1];
          var store = $("div#store").text();
          var active_a = $("td.translate-full").prev("td").children("a");
          var active_uid = active_a.attr("id").match(/editlink([0-9]+)/)[1];
          restore_active_unit(store, active_uid);
          get_unit_edit(store, uid);
        }
      }
    });
});
