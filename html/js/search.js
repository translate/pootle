$(document).ready(function($) {

  /* Search input text */
  var focused = { color: "#000" }
  var unfocused = { color: "#aaa" }

  $('label.inputHint').each(function() {
    var label = $(this);
    var input = $('#' + label.attr('for'));
    if (input.attr("defaultValue")) {
      var initial = input.attr("defaultValue");
      var search = true;
    } else {
      var initial = label.hide().text().replace(':', '');
    }
    input.focus(function() {
      input.css(focused);
      if (input.val() == initial && !search) {
        input.val('');
      }
    }).blur(function() {
      if (input.val() == '') {
        input.val(initial).css(unfocused);
      } else if (search && input.val() == initial) {
        input.css(unfocused);
      }
    }).css(unfocused).val(initial);
  });

  /* Dropdown toggling */
  $("a.advancedlink").click(function(event) {
    event.preventDefault();
    $("div.advancedsearch").slideToggle();
   }).toggle(
     function() {
       $("img.togglesearch").attr("src", "/html/images/bullet_arrow_up.png");
     },
     function() {
       $("img.togglesearch").attr("src", "/html/images/bullet_arrow_down.png");
     }
   );

});

