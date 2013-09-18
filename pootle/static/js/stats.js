(function ($) {

  window.PTL = window.PTL || {};

  PTL.stats = {

    init: function (options) {
      this.url = options.url;
      this.check_url = options.check_url;

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
          $.ajax({
            url: PTL.stats.check_url,
            success: function (data) {
              node.hide();
              node.find('.js-checks').each(function(e) {
                var empty = true,
                    $cat = $(this);

                $cat.find('.js-check').each(function(e) {
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
    nice_percentage: function(part, total) {
      var percentage = total ? part / total * 100 : 0;
      if (99 < percentage && percentage < 100) {
        return 99
      }
      if (0 < percentage && percentage < 1) {
        return 1
      }
      return Math.round(percentage)
    },
    update_progressbar: function ($td, item) {
      var translated = PTL.stats.nice_percentage(item.translated, item.total),
          fuzzy = PTL.stats.nice_percentage(item.fuzzy, item.total),
          untranslated = 100 - translated - fuzzy,
          $legend = $('<span>').html($td.find('script').text());

      untranslated = untranslated < 0 ? 0 : untranslated;

      $legend.find('.value.translated').text(translated);
      $legend.find('.value.fuzzy').text(fuzzy);
      $legend.find('.value.untranslated').text(untranslated);

      $td.find('table').attr('title', $legend.html());

      function set_td_width($td, w) {
        w === 0 ? $td.hide() : $td.css('width', w + '%').show();
      }
      set_td_width($td.find('td.translated'), translated);
      set_td_width($td.find('td.fuzzy'), fuzzy);
      set_td_width($td.find('td.untranslated'), untranslated);
    },
    update_translation_stats: function ($tr, total, value) {
      if (value) {
        $tr.find('.stats-number a').html(value);
        $tr.find('.stats-percentage span').html(
          PTL.stats.nice_percentage(value, total)
        );
        $tr.show();
      } else {
        $tr.hide();
      }
    },
    update_action: function ($action, count) {
      $action.css('display', count > 0 ? 'inline-block' : 'none');
      $action.find('.counter').text(count);
    },
    update_item_stats: function($td, count) {
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
      $.ajax({
        url: this.url,
        dataType: 'json',
        async: true,
        success: function (data) {
          var $table = $('#content table.stats');
          PTL.stats.update_progressbar($('#progressbar'), data);

          for (var name in data.children) {
            var item = data.children[name],
                code = name.replace(/\./g, '-'),
                $td = $table.find('#total-words-' + code);

            PTL.stats.update_item_stats($td, item.total);

            var ratio = item.total === 0 ? 1 : item.translated / item.total;
            $table.find('#translated-ratio-' + code).text(ratio);

            $td = $table.find('#need-translation-' + code);
            PTL.stats.update_item_stats($td, item.total - item.translated);

            $td = $table.find('#suggestions-' + code);
            PTL.stats.update_item_stats($td, item.suggestions);

            $td = $table.find('#progressbar-' + code);
            PTL.stats.update_progressbar($td, item);

            if (item.lastaction) {
              $td = $table.find('#last-activity-' + code);
              $td.html(item.lastaction.snippet);
              $td.find('.last-action .action-text').show();
            }

            $td = $table.find('#critical-' + code);
            PTL.stats.update_item_stats($td, item.critical);
          }

          PTL.stats.update_action($('#action-view-all'), data.total);
          PTL.stats.update_action($('#action-continue'), data.total - data.translated);
          PTL.stats.update_action($('#action-fix-critical'), data.critical);
          PTL.stats.update_action($('#action-review'), data.suggestions);

          $('body').removeClass('js-not-loaded');

          PTL.stats.update_translation_stats($('#stats-total'), data.total, data.total);
          PTL.stats.update_translation_stats($('#stats-translated'), data.total, data.translated);
          PTL.stats.update_translation_stats($('#stats-fuzzy'), data.total, data.fuzzy);
          PTL.stats.update_translation_stats($('#stats-untranslated'), data.total,
            data.total - data.translated - data.fuzzy);

          if (callback) {
            callback(data);
          }
        }
      });
    },
    load_checks: function(callback) {
      $.ajax({
        url: this.url,
        dataType: 'json',
        async: true,
        success: function (data) {
          var $table = $('#top-stats table.stats');
        }
      });
    }
  };

}(jQuery));
