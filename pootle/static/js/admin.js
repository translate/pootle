$(document).ready(function () {
  /* Sorts language names within select elements */
  var ids = ["id_languages", "id_alt_src_langs", "-language",
             "-source_language"];

  $.each(ids, function (i, id) {
    var selects = $("select[id$='" + id + "']");
    $.each(selects, function (i, select) {
      var select = $(select);
      var options = $("option", select);

      if (options.length) {
        if (!select.is("[multiple]")) {
          var selected = $(":selected", select);
        }
        var opsarray = $.makeArray(options);
        opsarray.sort(function (a,b) {
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
  var slideTable = function (event) {
    event.preventDefault();
    var node = $("#" + $(event.target).data('target'));

    $.ajax({
      url: l('/admin/stats/more'),
      dataType: 'json',
      success: function (data) {
        var newstats = '';
        $(data).each(function () {
          newstats += '<tr><th scope="row">' + this[0] + '</th>'
                      + '<td class="stats-number">' + this[1] + '</td></tr>';
        });
        node.append(newstats);
        node.slideDown("fast");
        node.next("tbody").remove();
      },
      beforeSend: function () {
        $(document).off("click", ".slide", slideTable);
        node.spin();
      },
      complete: function () {
        node.spin(false);
      },
      error: function () {
        $(document).on("click", ".slide", slideTable);
      }
    });
  };
  $(".slide").bind('click', slideTable);

  /* Sets background color to table rows when checking selects */
  $("td.DELETE input[type=checkbox]").change(function (e) {
      $(this).parents("tr").toggleClass("delete-selected",
                                        $(e.target).is(":checked"));
  });
  $("td[class!=DELETE] input[type=checkbox]").change(function (e) {
    if (!$("input[type=checkbox][checked]",
        $(this).parent().siblings("td[class!=DELETE]")).length) {
      $(this).parents("tr").toggleClass("other-selected",
                                        $(e.target).is(":checked"));
    }
  });


  /* Selects all checkboxes */
  $("th input").click(function (e) {
      var className = e.target.id.split('-').reverse()[0];
      $("td." + className + " input").prop("checked",
                                           $(e.target).is(":checked"));
      $("td." + className + " input").change();
  });


  /* Initialise description data and form */
  $('#edit_settings, #show_settings').click(function(e) {
    _toggle_editing();
  });
  _init_description();

  function _toggle_editing() {
    $('.intro, .js-admin-description, #edit_settings, #show_settings, #hide_description').slideToggle();
  }
  function _init_description() {
    $(".intro,").filter(":not([dir])").bidi();
    $('.js-admin-description form').submit(function (e) {
      e.preventDefault();
      $.ajax({
        url: $(this).attr('action'),
        type: 'POST',
        data: $(this).formSerialize(), //from jquery.form.js
        success: function (data) {
          $('.intro').first().html(data.intro);
          $('.js-admin-description').html(data.form);
          _init_description();
          if (data.valid) {
            _toggle_editing();
          }
        }
      });
    });
  }

});


/* NoticeForm - helper function to show/hide certain UI elements in response
 * to the user's selections.
 */
function toggleEmailFields() {
  $('#id_email_header').toggle();
  $("label[for='id_email_header']").toggle();

  $('#id_restrict_to_active_users').toggle();
  $("label[for='id_restrict_to_active_users']").toggle();

};


function noticeFormInit() {
  /* Assuming the default is for the 'Send Email' check button to be unselected,
     let's by default hide the email related fields. */
  toggleEmailFields();

  /* Install a toggle hide/show on the 'Send Email' check button */
  $('#id_send_email').change(function()  {
    toggleEmailFields();
  });

  /* Install a toggle hide/show on the 'All Projects' check button */
  $('#id_project_all').change(function()  {
    if ($('#id_project_all').is(':checked')) {
      // if selected..
      $('#id_project_selection option').prop('selected', true);
      // then hide..
      $('#id_project_selection').hide();
      $("label[for='id_project_selection']").hide();
    } else {
      // else, unselect all...
      $('#id_project_selection option').prop('selected', false );
      // then show
      $('#id_project_selection').show();
      $("label[for='id_project_selection']").show();
    }
  });

  /* Install a toggle hide/show on the 'All Languages' check button */
  $('#id_language_all').change(function()  {
    if ($('#id_language_all').is(':checked')) {
      // if selected...
      $('#id_language_selection option').prop('selected', true);
      // then hide...
      $('#id_language_selection').hide();
      $("label[for='id_language_selection']").hide();
    } else {
      // else, unselect all...
      $('#id_language_selection option').prop('selected', false );
      // then show
      $('#id_language_selection').show();
      $("label[for='id_language_selection']").show();
    }
  });

};
