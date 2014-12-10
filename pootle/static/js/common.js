(function ($) {

  window.PTL = window.PTL || {};

  PTL.common = {

    init: function () {
      setInterval($.fn.tipsy.revalidate, 1000);

      $(".js-select2").select2({
        width: "resolve"
      });

      // Hide the help messages for the Select2 multiple selects.
      $("select[multiple].js-select2").siblings("span.help_text").hide();

      // Build the language picker.
      var picker = $("#js-language-picker");
      for (i in PTL.languages) {
        var code = PTL.languages[i][0];
        var lang = PTL.languages[i][1];
        picker.append($("<option>", {value: code}).text(lang));
      }
      var getLocale = function(lang) {
        var locale = lang.slice(0, lang.indexOf("-"));
        var country = lang.indexOf("-") != -1 ? lang.slice(lang.indexOf("-"), -1) : null;
        var generic;

        for (i in PTL.languages) {
          var code = PTL.languages[i][0];
          if (lang == code) {
            return code;
          } else if (code == locale) {
            generic = code;
          }
        }
        return generic;
      }
      // select2 the picker separately because we want to give it a dynamic
      // width.
      picker.select2({dropdownCssClass: 's2js-freefloat-drop'})
        .select2("val", getLocale(picker.attr("default")))
        .on("change", function(e) {
            $.cookie("django_language", e.val, {path: "/"});
            location.reload();
        });

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

      /* Page sidebar tab display */
      $(document).on('click', '.js-sidebar-tab-display', function () {
        $('.js-sidebar-pane').hide();
        $('.js-sidebar-tab-display').removeClass('active-sidebar-tab');
        $('#' + $(this).attr('data-target')).show();
        $(this).addClass('active-sidebar-tab');
      });

      /* Popups */
      $(document).magnificPopup({
        type: 'ajax',
        delegate: '.js-popup-ajax',
        mainClass: 'popup-ajax'
      });
      $('.js-popup-inline').magnificPopup();

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

      // Save a detached copy of the table that we will reuse when resetting
      // filtering.
      var $projectTable = $("table#project");
      var $projectTableParent = $projectTable.parent();
      $projectTable.attr("id", "project-detached").detach();
      $projectTable.clone().attr("id", "project").appendTo($projectTableParent);
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

    fixSidebarTabs: function () {
      var sidebarTabsCount = $('.js-sidebar-tab-display').length;

      if (sidebarTabsCount === 1) {
        $('#sidebar-tabs').hide();
      } else if (sidebarTabsCount > 1) {
        $('.js-sidebar-pane').hide();
        if (!$('.active-sidebar-tab').length) {
          $('.js-sidebar-tab-display:first').addClass('active-sidebar-tab');
        }
        $('.active-sidebar-tab').trigger('click');
      }
    },

    fixSidebarHeight: function () {
      var $announceSidebar = $('#js-announcement-sidebar-pane'),
          $actionsSidebar = $('#js-actions-sidebar-pane'),
          $instructSidebar = $('#js-instructions-sidebar-pane'),
          annHeight = $announceSidebar.length ? $announceSidebar.height() : 0,
          actsHeight = $actionsSidebar.length ? $actionsSidebar.height() : 0,
          instHeight = $instructSidebar.length ? $instructSidebar.height() : 0,
          maxSidebarPanesHeight = Math.max(annHeight, actsHeight, instHeight);

      if (!maxSidebarPanesHeight) {
        // If there is no sidebar.
        return;
      }

      var $body = $('#body'),
          $sidebarTabs = $('#sidebar-tabs'),
          bodyHeight = $body.height(),
          bodyPadding = parseInt($body.css('padding-bottom'), 10),
          contentAreaHeight = $('#wrapper').height() - $body.offset().top -
                              bodyPadding,
          sidebarTabsHeight = $sidebarTabs.length ? $sidebarTabs.height() : 0,
          sidebarHeight = sidebarTabsHeight + maxSidebarPanesHeight +
                          $('#footer').height() + bodyPadding,
          newHeight = Math.max(contentAreaHeight, sidebarHeight);

      if (bodyHeight < contentAreaHeight) {
        $body.css('height', newHeight);
      }
    }

  };

}(jQuery));

$(function () {
  PTL.common.init();
});
