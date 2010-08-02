$(document).ready(function() {

  $(".collapse").click(function(event) {
    event.preventDefault();
    $("tbody.collapsethis").slideToggle("fast");
  });

});
