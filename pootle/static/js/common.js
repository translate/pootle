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

      // Append fragment identifiers for login redirects
      $('#navbar').on('focus click', '#js-login', function (e) {
        var $anchor = $(this),
            currentURL = $anchor.attr('href'),
            newURL = currentURL,
            hashIndex = currentURL.indexOf(encodeURIComponent('#')),
            hash = PTL.utils.getHash();

        if (hashIndex !== -1) {
          newURL = currentURL.slice(0, hashIndex);
        }
        if (hash !== '') {
          newURL = [
            newURL, encodeURIComponent(hash)
          ].join(encodeURIComponent('#'));
        }
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

      $(document).on("click", ".js-popup-tweet", function(e) {
        var width = 500;
        var height = 260;
        var left = (screen.width / 2) - (width / 2);
        var top = (screen.height / 2) - (height / 2);
        window.open(e.currentTarget.href, "_blank", "width="+width+",height="+height+",left="+left+",top="+top);
        return false;
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

    fixSidebarHeight: function () {
      var $body = $('#body'),
          bodyHeight = $body.height(),
          bodyPadding = parseInt($body.css('padding-bottom'), 10),
          contentAreaHeight = $('#wrapper').height() - $body.offset().top -
                              bodyPadding,
          sidebarHeight = $('#sidebar #staticpage').height() +
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

$(window).load(function () {
  $('body').removeClass('preload');
});
