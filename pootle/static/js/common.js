(function ($) {

  window.PTL = window.PTL || {};

  PTL.common = {

    init: function () {
      PTL.utils.makeSelectableInput('#js-select-language',
        {
          allowClear: true,
          dropdownAutoWidth: true,
          dropdownCssClass: 'breadcrumb-dropdown',
          placeholder: gettext("All Languages"),
          width: 'off'
        },
        function (e) {
          var langCode = $(this).val(),
              projectCode = $('#js-select-project').val();
          PTL.common.navigateTo(langCode, projectCode);
      });
      PTL.utils.makeSelectableInput('#js-select-project',
        {
          allowClear: true,
          dropdownAutoWidth: true,
          dropdownCssClass: 'breadcrumb-dropdown',
          placeholder: gettext("All Projects"),
          width: 'off'
        },
        function (e) {
          var projectCode = $(this).val(),
              langCode = $('#js-select-language').val();
          PTL.common.navigateTo(langCode, projectCode);
      });

      /* Collapsing functionality */
      $(document).on("click", ".collapse", function (e) {
        e.preventDefault();
        $(this).siblings(".collapsethis").slideToggle("fast");

        if ($("textarea", $(this).next("div.collapsethis")).length) {
          $("textarea", $(this).next("div.collapsethis")).focus();
        }
      });

      /* Popups */
      $('.js-popup-ajax').magnificPopup({
        type: 'ajax',
        mainClass: 'popup-ajax'
      });
      $('.js-popup-inline').magnificPopup();

      /* Path summary */
      $(document).on("click", "#js-path-summary", function (e) {
        e.preventDefault();
        var node = $("#" + $(this).data('target')),
            $textNode = $(this),
            data = node.data();

        function hideShow() {
          node.slideToggle('slow', 'easeOutQuad', function () {
            node.data('collapsed', !data.collapsed);
            var newText = data.collapsed ? gettext('Expand details') : gettext('Collapse details');
            $textNode.text(newText);
          });
        }

        if (data.loaded) {
          hideShow();
        } else {
          var url = $(this).attr('href');
          $.ajax({
            url: url,
            success: function (data) {
              node.html(data).hide();
              node.data('loaded', true);
              hideShow();
            },
            beforeSend: function () {
              node.spin();
            },
            complete: function () {
              node.spin(false);
            },
          });
        }
      });

      /* Overview actions */
      $("#overview-actions").on("click", ".js-overview-actions-delete-path",
        function (e) {
          return confirm(gettext("Are you sure you want to continue?") + "\n" +
                         gettext("This operation cannot be undone."));
      });

      /* Generic toggle */
      $(document).on("click", ".js-toggle", function (e) {
        e.preventDefault();
        var target = $(this).attr("href") || $(this).data("target");
        $(target).toggle();
      });

      /* Sorts language names within select elements */
      var ids = ["id_languages", "id_alt_src_langs", "-language",
                 "-source_language"];

      $.each(ids, function (i, id) {
        var $selects = $("select[id$='" + id + "']");

        $.each($selects, function (i, select) {
          var $select = $(select);
          var options = $("option", $select);

          if (options.length) {
            if (!$select.is("[multiple]")) {
              var selected = $(":selected", $select);
            }

            var opsArray = $.makeArray(options);
            opsArray.sort(function (a, b) {
              return PTL.utils.strCmp($(a).text(), $(b).text());
            });

            options.remove();
            $select.append($(opsArray));

            if (!$select.is("[multiple]")) {
              $select.get(0).selectedIndex = $(opsArray).index(selected);
            }
          }
        });
      });

      /* Toggle visibility of tagging related elements */
      $("#js-toggle-tags").show();
      $("#js-toggle-tags").click(function (event) {
        event.preventDefault();
        $(".js-tags").slideToggle('slow', 'easeOutQuad', function () {
          if ($(".js-tags").is(":hidden")) {
            $("#js-toggle-tags-text").text(gettext("Show tags"));
            $.cookie('showtags', 'false', {path: '/'});
          } else {
            $("#js-toggle-tags-text").text(gettext("Hide tags"));
            $.cookie('showtags', 'true', {path: '/'});
          }
        });
      });

      /* Launch the tag creation dialog in TP overview */
      $(".js-add-tag-popup").magnificPopup({
        key: '#js-add-tag-dialog',
        focus: '#js-tag-form-name',
        callbacks: {
          close: function() {
            // If add tag dialog is closed, the form fields must be cleaned
            // and the error messages must be removed.
            $("#js-tag-form-name").val("");
            $("#js-tag-form-slug").val("");
            $("#js-add-tag-form .errorlist").remove();
          }
        }
      });

      $(document).on("mouseenter", ".tag-list li", function () {
        $(this).children('.tag-remove').show();
      });

      $(document).on("mouseleave", ".tag-list li", function () {
        $(this).children('.tag-remove').hide();
      });

      $(document).on("click", ".tag-remove", function (event) {
        event.preventDefault();

        var $parent = $(this).parent()

        $.post($(this).attr('href'), function (data, textStatus, jqXHR) {
          if (jqXHR.status === 201) {
            // Tag was removed, delete the DOM element.
            $parent.remove();
          };
        }, "html");
      });

      /* Handle add tag form using AJAX */
      $(document).on("submit", "#js-add-tag-form", function (event) {
        // Avoid visiting form action.
        event.preventDefault();

        // Get tag name to generate a slug.
        var tagname = $("#js-tag-form-name").val().toLowerCase();

        // Set the tag name to lowercase to allow specifying names with any
        // case.
        $("#js-tag-form-name").val(tagname);

        // Replace invalid characters for slug with hyphens.
        var tagslug = tagname.replace(/[^a-z0-9-]/g, "-");

        // Replace groups of hyphens with a single hyphen.
        tagslug = tagslug.replace(/-{2,}/g, "-");

        // Remove leading and trailing hyphens.
        tagslug = tagslug.replace(/^-|-$/g, "");

        // Set the slug for the tag before submitting the form.
        $("#js-tag-form-slug").val(tagslug);

        // Submit the form through AJAX.
        var action = $("#js-add-tag-form").attr('action');
        var formData = $("#js-add-tag-form").serializeObject();

        $.post(action, formData, function (data, textStatus, jqXHR) {
          if (jqXHR.status === 201) {
            // Tag was added, replace the old tags list with the new one.

            if ($("#js-tags-tp").length) {
              // Project overview.
              var tp = $("#js-tags-tp option:selected").val();
              $('#js-tag-tp-' + tp + ' ul').html(data);
              $('#js-tag-tp-hidden-' + tp + ' ul').html(data);
            } else {
              // Translation project overview.
              $('.tag-list').html(data);
            }

            $.magnificPopup.close();
          } else if (jqXHR.status === 204) {
            // Tag was already applied, so close the currently opened popup.
            $.magnificPopup.close();
          } else if (jqXHR.status === 200) {
            // Form is invalid, so display it again with error messages.
            $("#js-add-tag-form").replaceWith(data);
          };
        }, "html");
      });

      /* Launch the tag creation dialog for a TP in project overview */
      $(document).on("click", ".js-project-add-tag-popup", function (event) {
        event.preventDefault();
        var tp = $(this).parent().prop("id");

        // Make sure that the id retrieved is a correct one.
        if (/^js-tag-tp-/.test(tp)) {
          // Get translation project PK from the retrieved id.
          tp = tp.split("-").pop();

          // Set the translation project in the form.
          $("#js-tags-tp option:selected").prop("selected", false);
          $('#js-tags-tp option[value="' + tp + '"]').prop("selected", true);

          // Open the dialog.
          $(this).magnificPopup({
            key: '#js-add-tag-dialog',
            focus: '#js-tag-form-name',
            callbacks: {
              close: function() {
                // If add tag dialog is closed, the form fields must be
                // cleaned and the error messages must be removed.
                $("#js-tag-form-name").val("");
                $("#js-tag-form-slug").val("");
                $("#js-add-tag-form .errorlist").remove();
              }
            }
          });
          $(this).magnificPopup('open');
        }
      });

      /* Hide the "Filter" button in the tag filtering form */
      $("#js-filter-form-button").hide();

      /* Dynamic filtering using tags */
      $("#js-tag-filtering").on("change", function (event) {
        // If there are no tag filters.
        if (event.val.length === 0) {
          // Remove the filtered table and show the original one.
          $("table#project-filtered").remove();
          $("table#project").show();
          // If tags are not hidden.
          if ($.cookie('showtags') === 'true') {
            $("table#project tbody tr").show();
          } else {
            $("table#project tbody tr:not(.js-tags)").show();
          };
        } else {
          // Get the filter tags names since Select2 only provides their keys.
          var filterTags = [];

          $.each(event.val, function (i, tagPK) {
            filterTags.push($("#js-tag-filtering option[value='" + tagPK +
                              "']").text());
          });

          // Iterate over all translation project rows, excluding the ones with
          // tagging data.
          var foundTags = [];

          $("table#project").hide();
          $filtered = $("table#project").clone();
          $filtered.attr("id", "project-filtered");

          // Cleanup table sorting stuff, we will re-sort.
          $filtered.find(".icon-ascdesc, .icon-asc, .icon-desc").remove();
          $filtered.find("th").removeClass("sorttable_sorted");
          $filtered.find("th").removeClass("sorttable_sorted_reverse");

          // Remove tags rows, will be re-added when sorting.
          $filtered.find(".tags-row").remove();

          $filtered.insertBefore("table#project");
          $filtered.show();

          $("table#project-filtered tbody tr:not(.js-tags)").each(function () {
            // Get all the tags applied to the current translation project.
            $(this).find("ul.tag-list li").each(function () {
              foundTags.push($(this).find(".js-tag-item").text());
            });

            // Get all the filter tags that the current translation project
            // matches.
            matchingFilters = $.grep(foundTags, function(element, index){
              return $.inArray(element, filterTags) !== -1;
            });

            // If the current translation project matches all the filter tags.
            if (matchingFilters.length === filterTags.length) {
              // Show the current translation project.
              $(this).show();
            } else {
              // Hide the current translation project.
              $(this).remove();
            };

            foundTags = [];
          });

          // Sort the filtered table.
          sorttable.makeSortable($filtered.get(0));
        };
      });
    },

    /* Navigates to `languageCode`, `projectCode` while retaining the
     * current context when applicable */
    navigateTo: function (languageCode, projectCode) {
      var curProject = $('#js-select-project').data('initial-code'),
          curLanguage = $('#js-select-language').data('initial-code'),
          curUrl = window.location.toString(),
          newUrl = curUrl,
          langChanged = languageCode !== curLanguage,
          projChanged = projectCode !== curProject,
          hasChanged = langChanged || projChanged;

      if (!hasChanged) {
        return;
      }

      if (languageCode === '' && projectCode === '') {
        newUrl = l('/');
      } else if (languageCode === '' && projectCode !== '') {
        newUrl = l(['', 'projects', projectCode].join('/'));
      } else if (languageCode !== '' && projectCode === '') {
        newUrl = l(['', languageCode].join('/'));
      } else if (languageCode !== '' && projectCode !== '') {
        if (projChanged) {
          newUrl = l(['', languageCode, projectCode].join('/'));
        } else if (langChanged) {
          if (curLanguage === '') {
            newUrl = curUrl.replace('projects/' + curProject,
                                    languageCode + '/' + curProject);
          } else {
            newUrl = curUrl.replace(curLanguage + '/' + curProject,
                                    languageCode + '/' + curProject)
                           .replace(/(\#|&)unit=\d+/, '');
          }
        }
        var changed = projChanged ? 'project' : 'language';
        $.cookie('user-choice', changed, {path: '/'});
      }

      window.location.href = newUrl;
    },

    /* Updates the disabled state of an input button according to the
     * checked status of input checkboxes.
     */
    updateInputState: function (checkboxSelector, inputSelector) {
      var $checkbox = $(checkboxSelector);
      if ($checkbox.length) {
        function updateInputState($checkboxes, $input) {
          if ($checkboxes.length === $checkboxes.filter(':checked').length) {
            $input.removeAttr('disabled');
          } else {
            $input.attr('disabled', 'disabled');
          }
        }
        var $input = $(inputSelector);
        updateInputState($checkbox, $input);
        $checkbox.change(function () {
          updateInputState($checkbox, $input);
        });
      }
    },

    /* Updates relative dates */
    updateRelativeDates: function () {
      $('.js-relative-date').each(function (i, e) {
        $(e).text(PTL.utils.relativeDate(Date.parse($(e).attr('datetime'))));
      });
    },

    submitAgreementForm: function () {
      var $agreementBox = $('.js-agreement-box'),
          $agreementForm = $('.js-agreement-form');
      $agreementBox.spin();
      $agreementBox.css({opacity: .5});

      $.ajax({
        url: $agreementForm.attr('action'),
        type: 'POST',
        data: $agreementForm.serializeObject(),
        success: function (data) {
          $.magnificPopup.close();
        },
        complete: function (xhr) {
          $agreementBox.spin(false);
          $agreementBox.css({opacity: 1});

          if (xhr.status === 400) {
            var form = $.parseJSON(xhr.responseText).form;
            $agreementBox.parent().html(form);
          }
        }
      });
    }

  };

}(jQuery));

$(function ($) {
  PTL.zoom.init();
  PTL.common.init();

  $(".js-select2").select2({
    width: "resolve"
  });
  // Hide the help messages for the Select2 multiple selects.
  $("select[multiple].js-select2").siblings("span.help_text").hide();
});

// We can't use `e.persisted` here. See bug 2949 for reference
window.addEventListener('pageshow', function (e) {
  var selectors = ['#js-select-language', '#js-select-project'];
  for (var i=0; i<selectors.length; i++) {
    var $el = $(selectors[i]),
        initial = $el.data('initial-code');
    $el.select2('val', initial);
  }
}, false);
