(function ($) {

  window.PTL = window.PTL || {};

  PTL.common = {

    init: function () {
      setInterval($.fn.tipsy.revalidate, 1000);

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
      PTL.utils.makeSelectableInput('#js-select-resource',
        {
          allowClear: true,
          dropdownAutoWidth: true,
          dropdownCssClass: 'breadcrumb-dropdown',
          placeholder: gettext("All Resources"),
          width: 'off'
        },
        function (e) {
          alert($(this).val());
        }
      );

      // Append fragment identifiers for login redirects
      $('#navbar').on('focus click', '#js-login', function (e) {
        var $anchor = $(this),
            currentURL = $anchor.attr('href'),
            cleanURL = currentURL,
            hashIndex = currentURL.indexOf(encodeURIComponent('#')),
            newURL;

        if (hashIndex !== -1) {
          cleanURL = currentURL.slice(0, hashIndex);
        }
        newURL = [cleanURL, encodeURIComponent(window.location.hash)].join('');
        $anchor.attr('href', newURL);
      });

      /* Collapsing functionality */
      $(document).on("click", ".collapse", function (e) {
        e.preventDefault();
        $(this).siblings(".collapsethis").slideToggle("fast");

        if ($("textarea", $(this).next("div.collapsethis")).length) {
          $("textarea", $(this).next("div.collapsethis")).focus();
        }
      });

      /* Page sidebar */
      $(document).on('click', '.js-sidebar-toggle', function () {
        var $sidebar =  $('.js-sidebar'),
            openClass = 'sidebar-open',
            cookieName = 'project-announcements',
            cookieData = JSON.parse($.cookie(cookieName)) || {};

        $sidebar.toggleClass(openClass);

        cookieData.isOpen = $sidebar.hasClass(openClass);
        $.cookie(cookieName, JSON.stringify(cookieData), {path: '/'});
      });

      /* Popups */
      $(document).magnificPopup({
        type: 'ajax',
        delegate: '.js-popup-ajax',
        mainClass: 'popup-ajax'
      });
      $('.js-popup-inline').magnificPopup();

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
        newUrl = l('/projects/');
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
    },

    fixSidebarHeight: function () {
      var $body = $('#body'),
          bodyHeight = $body.height(),
          contentAreaHeight = $('#wrapper').height() - $body.offset().top -
                              parseInt($body.css('padding-bottom'), 10),
          sidebarHeight = $('#sidebar #staticpage').height() +
                          $('#footer').height(),
          newHeight = Math.max(contentAreaHeight, sidebarHeight);

      if (bodyHeight < contentAreaHeight) {
        $body.css('height', newHeight);
      }
    }

  };

}(jQuery));

$(function ($) {
  PTL.zoom.init();
  PTL.common.init();

  $(".js-select2").select2({
    width: "resolve"
  });

  $(".js-breadcrumb").css("visibility", "visible");

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
