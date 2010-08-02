$(document).ready(function() {
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

});
