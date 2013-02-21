(function ($) {

  window.PTL = window.PTL || {};

  PTL.common = {

    init: function () {
      var projectLangsSelector = '#js-select-language',
          projectLangsUrl = $(projectLangsSelector).data('url');

      PTL.utils.makeSelectableInput(projectLangsSelector, projectLangsUrl,
        function (e) {
          var langCode = $(this).val();
          PTL.common.navigateToLang(langCode);
      });

      /* Collapsing functionality */
      $(document).on("click", ".collapse", function (e) {
        e.preventDefault();
        $(this).siblings(".collapsethis").slideToggle("fast");

        if ($("textarea", $(this).next("div.collapsethis")).length) {
          $("textarea", $(this).next("div.collapsethis")).focus();
        }
      });

      /* Fancybox on links */
      $(document).on("click", "a.fancybox", function (e) {
        e.preventDefault();
        $.fancybox({'href': $(e.target).attr('href'), 'type': 'ajax'});
      });

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
      $("#overview-actions").on("click", ".js-overview-actions-upload",
        function (e) {
          e.preventDefault();
          $.fancybox("#upload");
      });
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
    },

    /* Navigates to `langCode` while retaining the current context */
    navigateToLang: function (langCode) {
      var curProject = $('#js-select-project').data('code'),
          curLanguage = $('#js-select-language').data('code'),
          curUrl = window.location.toString();

      if (langCode === curLanguage) {
        return;
      }

      var newUrl = curUrl.replace(curLanguage + '/' + curProject,
                                  langCode + '/' + curProject)
                         .replace(/(\?|&)unit=\d+/, '');
      window.location.href = newUrl;
    }

  };

})(jQuery);

$(function ($) {
  PTL.zoom.init();
  PTL.common.init();
});
