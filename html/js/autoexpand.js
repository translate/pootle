$(document).ready(function() {
    // Pootle namespace
    $.pootle = {};

    // Set initial focus on page load
    var initialFocus = $(".translate-original-focus textarea");
    initialFocus.focus();
    $.pootle.focusedElement = initialFocus.get(0);

    // Update focus when appropriate
    $(".focusthis").focus(function(e) {
      $.pootle.focusedElement = e.target;
    });

    // Write TM results into the currently focused element
    $(".writetm").click(function() {
      var tmtext = $(".tm-translation", this).html();
      $($.pootle.focusedElement).replaceSelection(tmtext);
    });

    // Write special chars into the currently focused element
    $(".writespecial").click(function() {
      var specialtext = $(this).html();
      $($.pootle.focusedElement).replaceSelection(specialtext);
    });

    $(".copyoriginal").click(function() {
      var transid = $(this).parent().parent().attr("id");
      var elementNumber = transid.replace("trans", "")
      var enelement = $("#orig-pure" + elementNumber + "-0");
      var envalue = enelement.val().replace("\n", "\\n\n", "g").replace("\t", "\\t", "g");

      // no plurals
      var trelement = $("#areatrans" + elementNumber);
      if (trelement.length != 0) {
        trelement.val(envalue);
        trelement.focus();
        return;
      }

      //plurals
      var trelements = $("[id^=areatrans" + elementNumber + "-]");
      var enplelement = $("#orig-pure" + elementNumber + "-1");
      var enplvalue = enplelement.val().replace("\n", "\\n\n", "g").replace("\t", "\\t", "g");
      $.each(trelements, function(i) {
        newval = i == 0 ? envalue : enplvalue;
        $(this).val(newval);
        $(this).focus();
      });
    });

});
