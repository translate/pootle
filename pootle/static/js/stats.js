(function ($) {

  window.PTL = window.PTL || {};

  PTL.stats = {

    init: function (options) {
      this.pootlePath = options.pootlePath;

      /* Path summary */
      $(document).on("click", "#js-path-summary", function (e) {
        e.preventDefault();
        var node = $("#" + $(this).data('target')),
            $textNode = $(this).find(".js-label"),
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
          $('body').spin();
          var url = l('/xhr/stats/checks/'),
              reqData = {
                path: PTL.stats.pootlePath
              };
          $.ajax({
            url: url,
            data: reqData,
            success: function (data) {
              node.hide();
              node.find('.js-checks').each(function (e) {
                var empty = true,
                    $cat = $(this);

                $cat.find('.js-check').each(function (e) {
                  var $check = $(this),
                      code = $(this).data('code');
                  if (code in data) {
                    empty = false;
                    $check.show();
                    $check.find('.check-count a').html(data[code]);
                  } else {
                    $check.hide();
                  }
                });

                $cat.toggle(!empty);
              });

              node.data('loaded', true);
              hideShow();
            },
            complete: function () {
              $('body').spin(false);
            },
          });
        }
      });

    },

    nicePercentage: function (part, total) {
      var percentage = total ? part / total * 100 : 0;
      if (99 < percentage && percentage < 100) {
        return 99;
      }
      if (0 < percentage && percentage < 1) {
        return 1;
      }
      return Math.round(percentage);
    },

    updateProgressbar: function ($td, item) {
      var translated = PTL.stats.nicePercentage(item.translated, item.total),
          fuzzy = PTL.stats.nicePercentage(item.fuzzy, item.total),
          untranslated = 100 - translated - fuzzy,
          $legend = $('<span>').html($td.find('script').text());

      untranslated = untranslated < 0 ? 0 : untranslated;

      $legend.find('.value.translated').text(translated);
      $legend.find('.value.fuzzy').text(fuzzy);
      $legend.find('.value.untranslated').text(untranslated);

      $td.find('table').attr('title', $legend.html());

      function setTdWidth($td, w) {
        w === 0 ? $td.hide() : $td.css('width', w + '%').show();
      }
      setTdWidth($td.find('td.translated'), translated);
      setTdWidth($td.find('td.fuzzy'), fuzzy);
      setTdWidth($td.find('td.untranslated'), untranslated);
    },

    updateTranslationStats: function ($tr, total, value) {
      $tr.find('.stats-number a').html(value);
      $tr.find('.stats-percentage span').html(
        PTL.stats.nicePercentage(value, total)
      );
      $tr.find('.stats-percentage').show();
    },

    updateAction: function ($action, count) {
      $action.toggle(count > 0);
      $action.find('.counter').text(count);
    },

    updateItemStats: function ($td, count) {
      if (count) {
        $td.removeClass('zero');
        $td.addClass('non-zero');
        $td.find('a').html(count);
      } else {
        $td.find('a').html('');
        $td.addClass('zero');
        $td.removeClass('non-zero');
      }
    },

    load: function (callback) {
      var url = l('/xhr/stats/overview/'),
          reqData = {
            path: this.pootlePath
          };
      $.ajax({
        url: url,
        data: reqData,
        dataType: 'json',
        async: true,
        success: function (data) {
          var $table = $('#content table.stats');
          PTL.stats.updateProgressbar($('#progressbar'), data);

          for (var name in data.children) {
            var item = data.children[name],
                code = name.replace(/\./g, '-'),
                $td = $table.find('#total-words-' + code);

            PTL.stats.updateItemStats($td, item.total);

            var ratio = item.total === 0 ? 1 : item.translated / item.total;
            $table.find('#translated-ratio-' + code).text(ratio);

            $td = $table.find('#need-translation-' + code);
            PTL.stats.updateItemStats($td, item.total - item.translated);

            $td = $table.find('#suggestions-' + code);
            PTL.stats.updateItemStats($td, item.suggestions);

            $td = $table.find('#progressbar-' + code);
            PTL.stats.updateProgressbar($td, item);

            if (item.lastaction) {
              $td = $table.find('#last-activity-' + code);
              $td.html(item.lastaction.snippet);
              $td.find('.last-action .action-text').show();
            }

            $td = $table.find('#critical-' + code);
            PTL.stats.updateItemStats($td, item.critical);
          }

          PTL.stats.updateAction($('#action-view-all'), data.total);
          PTL.stats.updateAction($('#action-continue'),
                                  data.total - data.translated);
          PTL.stats.updateAction($('#action-fix-critical'), data.critical);
          PTL.stats.updateAction($('#action-review'), data.suggestions);

          $('body').removeClass('js-not-loaded');

          PTL.stats.updateTranslationStats($('#stats-total'),
                                             data.total, data.total);
          PTL.stats.updateTranslationStats($('#stats-translated'),
                                             data.total, data.translated);
          PTL.stats.updateTranslationStats($('#stats-fuzzy'),
                                             data.total, data.fuzzy);
          var untranslated = data.total - data.translated - data.fuzzy;
          PTL.stats.updateTranslationStats($('#stats-untranslated'),
                                             data.total, untranslated);

          if (callback) {
            callback(data);
          }
        }
      });
    }
  };

}(jQuery));
