$(document).ready(function() {
    $("a[id^=editlink]").click(function(e) {
      e.preventDefault();
      if (!$(this).parent().next("td").hasClass("translate-full")) {
        // Retrieve unit i+1, if any
        var m = $(this).attr("id").match(/editlink([0-9]+)/);
        if (m) {
          var uid = m[1];
          // TODO: We should keep the store information stored
          // somewhere else in the DOM.
          var store = $("div#store").text();
          var view_url = l(store + '/unit/view/' + uid);
          $.getJSON(view_url, function(data) {
            if (data.success) {
              $(data.unit.source).each(function() {
                alert(this);
              });
              $(data.unit.target).each(function() {
                alert(this);
              });
              var oldunit = $("td.translate-full").parent("tr");
              oldunit.children().remove();
              $(this).parent().siblings().remove();
            } else {
              // TODO: provide a proper error message and not an alert
              alert("Something went wrong");
            }
          });
        }
      }
    });
});
