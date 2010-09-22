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
            display_view_unit(units[uid]);
          } else {
            // TODO: provide a proper error message and not an alert
            alert("Something went wrong");
            return false;
          }
        });
      } else {
        display_view_unit(units[uid]);
      }
    };

    var display_view_unit = function(unit) {
      $(unit.source).each(function() {
        alert(this);
      });
      $(unit.target).each(function() {
        alert(this);
      });
      // FIXME: This is only for the editing widget
      var oldunit = $("td.translate-full").parent("tr");
      oldunit.children().remove();
      $(this).parent().siblings().remove();
    };

    $("a[id^=editlink]").click(function(e) {
      e.preventDefault();
      if (!$(this).parent().next("td").hasClass("translate-full")) {
        // Retrieve unit i+1, if any
        var m = $(this).attr("id").match(/editlink([0-9]+)/);
        if (m) {
          var uid = m[1];
          var store = $("div#store").text();
          get_unit_view(store, uid);
        }
      }
    });
});
