$(document).ready(function() {
    $("a[id^=editlink]").click(function(e) {
      e.preventDefault();
      if (!$(this).parent().next("td").hasClass("translate-full")) {
        // Retrieve unit i+1, if any
        var m = $(this).attr("id").match(/editlink([0-9]+)/);
        if (m) {
          uid = m[1];
          var oldunit = $("td.translate-full").parent("tr");
          oldunit.children().remove();
          $(this).parent().siblings().remove();
        }
      }
    });
});
