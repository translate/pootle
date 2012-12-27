$(function () {

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


  /* Inline editing */

  $('.markup-body').filter(':not([dir])').bidi();

  if ($('.js-edit-details').length) {
    var $metaDesc = $('.js-ctx-meta-desc'),
        $editMetaDesc = $('.js-edit-ctx-meta-desc'),
        editMetaSelector = '#js-admin-edit-meta';

    $metaDesc.on('click', '.js-edit-details', function (e) {
      e.preventDefault();
      $metaDesc.hide();
      $editMetaDesc.show();
      $editMetaDesc.find('#id_description').focus();
    });

    $editMetaDesc.on('click', '.js-edit-details-cancel', function (e) {
      e.preventDefault();
      $metaDesc.show();
      $editMetaDesc.hide();
    });

    $editMetaDesc.on('submit', editMetaSelector, function (e) {
      e.preventDefault();

      $editMetaDesc.spin();
      $editMetaDesc.css({opacity: .5});

      $.ajax({
        url: $(this).attr('action'),
        type: 'POST',
        data: $(this).serializeObject(),
        success: function (data) {
          var $metaDescContent = $metaDesc.children().filter(':first');

          $editMetaDesc.hide();
          $editMetaDesc.html(data.form);

          $metaDescContent.replaceWith(data.description_html);
          $metaDesc.show();

          $('.markup-body').filter(':not([dir])').bidi();
        },
        complete: function (xhr) {
          $editMetaDesc.spin(false);
          $editMetaDesc.css({opacity: 1});

          if (xhr.status === 400) {
            var form = $.parseJSON(xhr.responseText).form;
            $(editMetaSelector).parent().html(form);
          }
        },
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
