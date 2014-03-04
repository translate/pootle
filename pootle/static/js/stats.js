(function ($) {

  window.PTL = window.PTL || {};

  PTL.stats = {

    init: function (options) {
      this.pootlePath = options.pootlePath;

      $(document).on("click", "#js-path-summary", PTL.stats.toggleChecks);
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
      if (item.total === 0) {
        $td.hide();
        return;
      }

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

    updatePathSummary: function ($pathSummary, data) {
      var incomplete = data.total - data.translated,
          translated = PTL.stats.nicePercentage(data.translated, data.total),
          summary;

      if (data.pathsummary.is_dir) {
        var fmt = ngettext('This folder has %s word, %s% of which is translated.',
                           'This folder has %s words, %s% of which are translated.',
                           data.total);
        summary = interpolate(fmt, [data.total, translated]);
      } else {
        var fmt = ngettext('This file has %s word, %s% of which is translated.',
                           'This file has %s words, %s% of which are translated.',
                           data.total);
        summary = interpolate(fmt, [data.total, translated]);
      }

      var $pathSummaryMore = $("<a />", {
        'id': 'js-path-summary',
        'href': data.pathsummary.summary_more_url,
        'text': gettext('Expand details'),
        'data-target': 'js-path-summary-more',
      });

      $pathSummary.append(
        $('<li/>').append(summary)
                  .append(' ')
                  .append($pathSummaryMore)
                  .append(data.pathsummary.goals_summary)
      );

      if (incomplete > 0) {
        var fmt = ngettext('Continue translation (%s word left)',
                           'Continue translation (%s words left)', incomplete);
        var $incomplete = $("<a />", {
          'class': 'path-incomplete',
          'href': data.pathsummary.incomplete_url,
          'text': interpolate(fmt, [incomplete]),
        });

        $pathSummary.append($('<li/>').append($incomplete));
      } else {
        var $incomplete = $("<a />", {
          'class': 'path-incomplete',
          'href': data.pathsummary.translate_url,
          'text': gettext('Translation is complete'),
        });

        $pathSummary.append($('<li/>').append($incomplete));
      }

      if (data.suggestions > 0) {
        var fmt = ngettext('Review suggestion (%s left)',
                           'Review suggestions (%s left)', data.suggestions);
        var $suggestions = $("<a />", {
          'class': 'path-incomplete',
          'href': data.pathsummary.suggestions_url,
          'text': interpolate(fmt, [data.suggestions]),
        });

        $pathSummary.append($('<li/>').append($suggestions));
      }
    },

    updateSummary: function ($summary, data) {
      var summary,
          percent = PTL.stats.nicePercentage(data.translated, data.total);
      summary = interpolate(gettext(', %s% translated'), [percent]);
      $summary.append(summary);
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
          var $table = $('#content table.stats'),
              now = parseInt(Date.now() / 1000, 10);
          PTL.stats.updateProgressbar($('#progressbar'), data);
          PTL.stats.updateSummary($('#summary'), data);
          PTL.stats.updatePathSummary($('#path-summary-head'), data);

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

          if ($table.length) {
            for (var name in data.children) {
              var item = data.children[name],
                  code = name.replace(/\./g, '-').replace(/@/g, '\\@'),
                  $td = $table.find('#total-words-' + code);

              PTL.stats.updateItemStats($td, item.total);

              var ratio = item.total === 0 ? 0 : item.translated / item.total;
              $table.find('#translated-ratio-' + code).text(ratio);

              $td = $table.find('#need-translation-' + code);
              PTL.stats.updateItemStats($td, item.total - item.translated);

              $td = $table.find('#suggestions-' + code);
              PTL.stats.updateItemStats($td, item.suggestions);

              $td = $table.find('#progressbar-' + code);
              PTL.stats.updateProgressbar($td, item);

              $td = $table.find('#last-activity-' + code);
              $td.html(item.lastaction.snippet);
              $td.attr('sorttable_customkey', now - item.lastaction.mtime);

              $td = $table.find('#critical-' + code);
              PTL.stats.updateItemStats($td, item.critical);
            }

            // Sort columns based on previously-made selections
            var sortCookie = $table.data('sort-cookie'),
                columnSort = sorttable.getSortCookie(sortCookie);

            if (columnSort !== null) {
              var $th = $('#' + columnSort.columnId);
              var sorted = $th.hasClass("sorttable_sorted");
              var sorted_reverse = $th.hasClass("sorttable_sorted_reverse");

              if (sorted || sorted_reverse) {
                // If already sorted, fire the event only if the other order is
                // desired.
                if (sorted && columnSort.order === "desc")
                  $th.click();
                else if (sorted_reverse && columnSort.order === "asc")
                  $th.click();
              } else {
                $th.click();

                // If the sorting order was descending, fire another click event
                if (columnSort.order === "desc")
                  $th.click();
              }
            }
          } else {
            $('#js-path-summary').click();
          }

          if (callback) {
            callback(data);
          }
        }
      });
    },

    /* Path summary */
    toggleChecks: function (e) {
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
        var url = $(this).attr('href'),
            reqData = {
              path: PTL.stats.pootlePath
            };
        $.ajax({
          url: url,
          data: reqData,
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
    }
  };

}(jQuery));
