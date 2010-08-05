$(document).ready(function() {
  /* Sorts language names within select elements */
  var ids = ["id_languages", "id_alt_src_langs", "-language",
             "-source_language"];

  $.each(ids, function(i, id) {
    var selects = $("select[id$='" + id + "']");
    $.each(selects, function(i, select) {
      var select = $(select);
      var options = $("option", select);

      if (options.length) {
        if (!select.is("[multiple]")) {
          var selected = $(":selected", select);
        }
        var opsarray = $.makeArray(options);
        opsarray.sort(function(a,b) {
          return $(a).text() > $(b).text()
        });
        options.remove();
        select.append($(opsarray));
        if (!select.is("[multiple]")) {
          select.get(0).selectedIndex = $(opsarray).index(selected);
        }
      }
    });
  });

  /* Sliding table within admin dashboard */
  $(".slide").click(function(event) {
    event.preventDefault();
    $("tbody.slidethis").slideDown("fast");
    $(this).parents("tbody").remove();
  });

  /* Sets background color to table rows when checking selects */
  $("td.DELETE input[type=checkbox]").click(function() {
      $(this).parents("tr").toggleClass("delete-selected");
  });
  $("td[class!=DELETE] input[type=checkbox]").click(function() {
      if (!$("input[type=checkbox][checked]",
             $(this).parent().siblings("td[class!=DELETE]")).length) {
        $(this).parents("tr").toggleClass("other-selected");
      }
  });

});
