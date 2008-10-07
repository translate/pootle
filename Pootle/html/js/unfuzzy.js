/*
 *  For future enhancements like multiple edit boxes, please note
 *  that the selector is based on a class, so it must be modified
 *  to get the textarea's element ID and select the checkbox to
 *  remove the "checked" attribute according to that value.
 */
$(document).ready(function() {
  var keepstate = false;
  $("textarea.translation").bind("keyup blur", function() {
    if (!keepstate && $(this).attr("defaultValue") != $(this).val()) {
      var checkbox = $("input.unfuzzy[checked]");
      checkbox.removeAttr("checked");
      checkbox.parent().animate({ backgroundColor: "#dafda5 !important" }, "fast")
                       .animate({ backgroundColor: "#f4f4f4 !important" }, "slow");
      $("textarea.translate-translation-fuzzy").each(function () {
        $(this).removeClass("translate-translation-fuzzy");
      });
      keepstate = true;
    }
  });
  $("input.unfuzzy").click(function() {
    keepstate = true;
  });
});
