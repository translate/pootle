(function ($) {

  window.PTL = window.PTL || {};

  PTL.stats = {

    init: function (options) {
      this.pootlePath = options.pootlePath;

      $(document).on("click", "#js-path-summary", PTL.stats.toggleChecks);
    },

    nicePercentage: function (part, total, noTotalDefault) {
      var percentage = total ? part / total * 100 : noTotalDefault;
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

      var translated = PTL.stats.nicePercentage(item.translated, item.total, 100),
          fuzzy = PTL.stats.nicePercentage(item.fuzzy, item.total, 0),
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

    updateSummary: function ($summary, data) {
      var percent = PTL.stats.nicePercentage(data.translated, data.total);
      $summary.append(interpolate(gettext(', %s% translated'), [percent]));
    },

    updateTranslationStats: function ($tr, total, value, noTotalDefault) {
      $tr.find('.stats-number a').html(value);
      $tr.find('.stats-percentage span').html(
        PTL.stats.nicePercentage(value, total, noTotalDefault)
      );
      $tr.find('.stats-percentage').show();
    },

    updateAction: function ($action, count) {
      $action.css('display', count > 0 ? 'inline-block' : 'none');
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

    updateLastUpdates: function (stats) {
      if (stats.lastupdated) {
        $('#js-last-updated').toggle(stats.lastupdated.snippet !== '');
        if (stats.lastupdated.snippet) {
          $('#js-last-updated .last-updated').html(stats.lastupdated.snippet);
        }
      }
      if (stats.lastaction) {
        $('#js-last-action').toggle(stats.lastaction.snippet !== '');
        if (stats.lastaction.snippet) {
          $('#js-last-action .last-action').html(stats.lastaction.snippet);
        }
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
        success: function (data) {
          var $table = $('#content table.stats'),
              now = parseInt(Date.now() / 1000, 10);
          PTL.stats.updateProgressbar($('#progressbar'), data);
          PTL.stats.updateSummary($('#summary'), data);

          PTL.stats.updateAction($('#js-action-view-all'), data.total);
          PTL.stats.updateAction($('#js-action-continue'),
                                 data.total - data.translated);
          PTL.stats.updateAction($('#js-action-fix-critical'), data.critical);
          PTL.stats.updateAction($('#js-action-review'), data.suggestions);
          PTL.stats.updateAction($('#js-action-next-goal'), data.nextGoal);

          $('body').removeClass('js-not-loaded');

          PTL.stats.updateTranslationStats($('#stats-total'),
                                           data.total, data.total, 100);
          PTL.stats.updateTranslationStats($('#stats-translated'),
                                           data.total, data.translated, 100);
          PTL.stats.updateTranslationStats($('#stats-fuzzy'),
                                           data.total, data.fuzzy, 0);
          var untranslated = data.total - data.translated - data.fuzzy;
          PTL.stats.updateTranslationStats($('#stats-untranslated'),
                                           data.total, untranslated, 0);
          PTL.stats.updateLastUpdates(data);

          if ($table.length) {
            for (var name in data.children) {
              var item = data.children[name],
                  code = name.replace(/[\.@]/g, '-'),
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

              $td = $table.find('#last-updated-' + code);
              $td.html(item.lastupdated.snippet);
              $td.attr('sorttable_customkey', now - item.lastupdated.creation_time);

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
          $iconNode = $(this).find("#js-expand-icon"),
          data = node.data();

      function hideShow() {
        node.data('collapsed', !data.collapsed);
        var newClass = data.collapsed ? 'icon-expand-stats' : 'icon-collapse-stats';
        var newText = data.collapsed ? gettext('Expand details') : gettext('Collapse details');
        $iconNode.attr('class', newClass);
        $iconNode.attr('title', newText);
        node.slideToggle('slow', 'easeOutQuad');
      }

      if (data.loaded) {
        hideShow();
      } else {
        var url = l('/xhr/stats/checks/'),
            reqData = {
              path: PTL.stats.pootlePath
            };
        $.ajax({
          url: url,
          data: reqData,
          success: function (data) {
            node.hide();
            if (Object.keys(data).length) {
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

              $('#js-stats-checks').show();
            }

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
