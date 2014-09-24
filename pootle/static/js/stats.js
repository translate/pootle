(function ($) {

  window.PTL = window.PTL || {};

  PTL.stats = {

    init: function (options) {
      this.pootlePath = options.pootlePath;
      this.processLoadedData(options.data);

      $(document).on("click", "#js-path-summary", PTL.stats.toggleChecks);
      $(document).on("click", "#autorefresh-notice", function () {
          PTL.stats.dirtyInterval = 1;
          PTL.stats.updateDirty();
      });
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

    processLoadedData: function (data, callback) {
      var $table = $('#content table.stats'),
          dirtySelector = '#top-stats, #translate-actions, #autorefresh-notice',
          now = parseInt(Date.now() / 1000, 10);

      $(dirtySelector).toggleClass('dirty', data.is_dirty);
      if (data.is_dirty) {
        $('#autorefresh-notice a').show();
        PTL.stats.dirtyInterval = 30;
        PTL.stats.dirtyIntervalId = setInterval(PTL.stats.updateDirty, 1000);
      }

      PTL.stats.updateProgressbar($('#progressbar'), data);
      PTL.stats.updateAction($('#js-action-view-all'), data.total);
      PTL.stats.updateAction($('#js-action-continue'),
                             data.total - data.translated);
      PTL.stats.updateAction($('#js-action-fix-critical'), data.critical);
      PTL.stats.updateAction($('#js-action-review'), data.suggestions);

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

          $td.parent().toggleClass('dirty', item.is_dirty);
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
            $td.attr('sorttable_customkey', now - item.lastaction.mtime);
          }

          $td = $table.find('#critical-' + code);
          PTL.stats.updateItemStats($td, item.critical);

          if (item.lastupdated) {
            $td = $table.find('#last-updated-' + code);
            $td.html(item.lastupdated.snippet);
            $td.attr('sorttable_customkey', now - item.lastupdated.creation_time);
          }
        }

        // Sort columns based on previously-made selections
        var sortCookie = $table.data('sort-cookie'),
            columnSort = sorttable.getSortCookie(sortCookie);
        if (columnSort !== null) {
          var $th = $('#' + columnSort.columnId);
          setTimeout(function() {
            $th.click();
            if (columnSort.order === "desc") {
              $th.click();
            }
          }, 1);
        }
      } else {
        setTimeout(function() {
          $('#js-path-summary').click();
        }, 1);
      }
      PTL.common.updateRelativeDates();

      if (callback) {
        callback(data);
      }
    },

    updateDirty: function () {
      if (--PTL.stats.dirtyInterval === 0) {
        $('body').spin();
        $('#autorefresh-notice a').hide();
        clearInterval(PTL.stats.dirtyIntervalId);
        setTimeout(function () {
          PTL.stats.load(function() {
            $('body').spin(false);
          });
        }, 250);
      }
      noticeStr = ngettext('%s second', '%s seconds', PTL.stats.dirtyInterval);
      noticeStr = interpolate(noticeStr, [PTL.stats.dirtyInterval], false);
      $('#autorefresh-notice strong').text(noticeStr);
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
          return this.processLoadedData(data, callback);
        }
      });
    },

    /* Path summary */
    toggleChecks: function (e) {
      e.preventDefault();
      var $node = $("#" + $(this).data('target')),
          $iconNode = $(this).find("#js-expand-icon"),
          data = $node.data();

      function hideShow() {
        $node.data('collapsed', !data.collapsed);
        var newClass = data.collapsed ? 'icon-expand-stats' : 'icon-collapse-stats';
        var newText = data.collapsed ? gettext('Expand details') : gettext('Collapse details');
        $iconNode.attr('class', newClass);
        $iconNode.attr('title', newText);
        $node.slideToggle('slow', 'easeOutQuad');
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
            $node.hide();
            if (Object.keys(data).length) {
              $node.find('.js-checks').each(function (e) {
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

            $node.data('loaded', true);
            hideShow();
          },
          complete: function () {
            $('body').spin(false);
          },
        });
      }
    }
  };

}(jQuery));
