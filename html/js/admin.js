$(document).ready(function() {

  $(".slide").click(function(event) {
    event.preventDefault();
    $("tbody.slidethis").slideDown("fast");
    $(this).parents("tbody").remove();
  });

});
