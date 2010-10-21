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
  var slide_table = function(event) {
    event.preventDefault();
    $.ajax({
      url: l('/admin/stats/more'),
      dataType: 'json',
      beforeSend: function() {
        $(".slide").unbind('click', slide_table);
      },
      error: function () {
        $(".slide").bind('click', slide_table);
      },
      success: function(data) {
        var newstats = '';
        $(data).each(function() {
          newstats += '<tr><th scope="row">' + this[0] + '</th>'
                      + '<td class="stats-number">' + this[1] + '</td></tr>';
        });
        $("tbody.slidethis").append(newstats);
        $("tbody.slidethis").slideDown("fast");
        $("tbody.slidethis").next("tbody").remove();
      }
    });
  };
  $(".slide").bind('click', slide_table);

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
