/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

var $ = require('jquery');

require('jquery-bidi');
require('jquery-easing');
require('jquery-utils');
require('sorttable');

var helpers = require('./helpers.js');


var nicePercentage = function (part, total, noTotalDefault) {
  var percentage = total ? part / total * 100 : noTotalDefault;
  if (99 < percentage && percentage < 100) {
    return 99;
  }
  if (0 < percentage && percentage < 1) {
    return 1;
  }
  return Math.round(percentage);
};


var onDataLoad = function () {
  $('body').spin(false);
};


function cssId(id) {
  return id.replace(/[\.@\+]/g, '-');
}


var stats = {

  init: function (options) {
    this.retries = 0;
    this.pootlePath = options.pootlePath;
    this.isAdmin = options.isAdmin;
    this.processLoadedData(options.data, undefined, true);

    $('td.stats-name').filter(':not([dir])').bidi();

    $(document).on('click', '#js-path-summary', this.toggleChecks.bind(this));
    $(document).on('click', '.js-stats-refresh', this.refreshStats.bind(this));

    $(document).on('click',
		   '#js-path-summary-more a',
		   this.appendDetailsOpenHash.bind(this));
    this.reopenDetails();
  },

  refreshStats: function (e) {
    e.preventDefault();
    this.dirtyBackoff = 1;
    this.updateDirty();
  },

  updateProgressbar: function ($td, item) {
    var translated = nicePercentage(item.translated, item.total, 100),
        fuzzy = nicePercentage(item.fuzzy, item.total, 0),
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
      nicePercentage(value, total, noTotalDefault)
    );
    $tr.find('.stats-percentage').show();
  },

  updateAction: function ($action, count) {
    $action.toggleClass('non-zero', !(count === 0));
    $action.find('.counter').text(count !== null ? count : '—');
  },

  updateItemStats: function ($td, count) {
    if (count) {
      $td.removeClass('zero');
      $td.removeClass('not-inited');
      $td.addClass('non-zero');
      $td.find('a').html(count);
    } else if (count === 0) {
      $td.find('a').html('');
      $td.addClass('zero');
      $td.removeClass('not-inited');
      $td.removeClass('non-zero');
    } else {
      $td.removeClass('zero');
      $td.removeClass('non-zero');
      $td.addClass('not-inited');
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

  processTableItem: function (item, code, $table, $td, now) {
    $td.parent().toggleClass('dirty', item.is_dirty);
    this.updateItemStats($td, item.total);

    var isFullRatio = item.total === 0 || item.total === null,
        ratio = isFullRatio ? 1 : item.translated / item.total;
    $table.find('#translated-ratio-' + code).text(ratio);

    $td = $table.find('#need-translation-' + code);
    var needTranslationCount = item.total !== null ?
      item.total - item.translated : null;
    this.updateItemStats($td, needTranslationCount);

    $td = $table.find('#suggestions-' + code);
    this.updateItemStats($td, item.suggestions);

    $td = $table.find('#progressbar-' + code);
    this.updateProgressbar($td, item);

    if (item.lastaction) {
      $td = $table.find('#last-activity-' + code);
      $td.removeClass('not-inited');
      $td.html(item.lastaction.snippet);
      $td.attr('sorttable_customkey', now - item.lastaction.mtime);
    }

    $td = $table.find('#critical-' + code);
    this.updateItemStats($td, item.critical);

    if (item.lastupdated) {
      $td = $table.find('#last-updated-' + code);
      $td.removeClass('not-inited');
      $td.html(item.lastupdated.snippet);
      $td.attr('sorttable_customkey', now - item.lastupdated.creation_time);
    }
  },

  processLoadedData: function (data, callback, firstPageLoad) {
    var $table = $('#content table.stats'),
        $vfoldersTable = $('#content .vfolders table.stats'),
        dirtySelector = '#top-stats, #translate-actions, #autorefresh-notice',
        now = parseInt(Date.now() / 1000, 10);

    $(dirtySelector).toggleClass('dirty', !!data.is_dirty);
    if (!!data.is_dirty) {
      this.dirtyBackoff = Math.pow(2, this.retries);
      this.updateDirtyBackoffCounter();
      $('.js-stats-refresh').show();
      this.dirtyBackoffId = setInterval(this.updateDirty.bind(this), 1000);
    }

    this.updateProgressbar($('#progressbar'), data);
    this.updateAction($('#js-action-view-all'), data.total);
    this.updateAction($('#js-action-continue'), data.total - data.translated);
    this.updateAction($('#js-action-fix-critical'), data.critical);
    this.updateAction($('#js-action-review'), data.suggestions);

    this.updateTranslationStats($('#stats-total'),
                                data.total, data.total, 100);
    this.updateTranslationStats($('#stats-translated'),
                                data.total, data.translated, 100);
    this.updateTranslationStats($('#stats-fuzzy'),
                                data.total, data.fuzzy, 0);
    var untranslated = data.total === null ? null :
      data.total - data.translated - data.fuzzy;
    this.updateTranslationStats($('#stats-untranslated'),
                                data.total, untranslated, 0);
    this.updateLastUpdates(data);

    if ($table.length) {
      // this is a directory that contains subitems
      var name, item, code, $td;

      for (name in data.children) {
        item = data.children[name];
        code = cssId(name);
        $td = $table.find('#total-words-' + code);

        this.processTableItem(item, code, $table, $td, now);
      }

      if ($vfoldersTable.length) {
        for (name in data.vfolders) {
          item = data.vfolders[name];
          code = cssId(name);
          $td = $vfoldersTable.find('#total-words-' + code);

          // Display only the virtual folders that must be displayed.
          if (this.isAdmin || item.isVisible) {
            this.processTableItem(item, code, $vfoldersTable, $td, now);
          } else {
            //FIXME vfolders might be added or removed since they can become
            // completely translated or stop being completely translated, so
            // they might be displayable after the initial load of the
            // browser.
            $td.parent().hide();
          }
        }

        // If all vfolders have been hidden (only table header is shown), then
        // also hide the whole table. Otherwise ensure the vfolders table is
        // displayed.
        if ($vfoldersTable.find('tr:visible').length === 1) {
          $vfoldersTable.hide();
        } else {
          $vfoldersTable.show();
        }
      }

      // Sort columns based on previously-made selections
      var sortCookie = $table.data('sort-cookie'),
          columnSort = sorttable.getSortCookie(sortCookie);
      if (columnSort !== null) {
        var $th = $('#' + columnSort.columnId);
        $th.removeClass('sorttable_sorted sorttable_sorted_reverse');
        setTimeout(function () {
          $th.click();
          if (columnSort.order === "desc") {
            $th.click();
          }
        }, 1);
      }
    } else {
      // this is a single store stats, let's expand its details
      // only on first page load, and unless it is already expanded
      if (firstPageLoad && $('#js-path-summary-more').data('collapsed')) {
        setTimeout(function () {
          $('#js-path-summary').click();
        }, 1);
      }

    }
    helpers.updateRelativeDates();

    if (callback) {
      callback(data);
    }
  },

  updateDirty: function () {
    if (--this.dirtyBackoff === 0) {
      $('body').spin();
      $('.js-stats-refresh').hide();
      clearInterval(this.dirtyBackoffId);
      setTimeout(function () {
        if (this.retries < 5) {
          this.retries++;
        }
        this.load(onDataLoad);
      }.bind(this), 250);
    }
    this.updateDirtyBackoffCounter();
  },

  updateDirtyBackoffCounter: function () {
    var noticeStr = ngettext('%s second', '%s seconds', this.dirtyBackoff);
    noticeStr = interpolate(noticeStr, [this.dirtyBackoff], false);
    $('#autorefresh-notice strong').text(noticeStr);
  },

  load: function (callback) {
    var url = l('/xhr/stats/'),
        reqData = {
          path: this.pootlePath
        };

    $.ajax({
      url: url,
      data: reqData,
      dataType: 'json',
      success: function (data) {
        return this.processLoadedData(data, callback);
      }.bind(this)
    });
  },

  /* Path summary */
  toggleChecks: function (e) {
    e.preventDefault();
    var $el = $(e.currentTarget),
        $node = $("#" + $el.data('target')),
        $iconNode = $el.find("#js-expand-icon"),
        data = $node.data();

    function hideShow() {
      $node.data('collapsed', !data.collapsed);
      var newClass = data.collapsed ? 'icon-expand-stats' : 'icon-collapse-stats';
      var newText = data.collapsed ? gettext('Expand details') : gettext('Collapse details');
      $iconNode.attr('class', newClass);
      $iconNode.attr('title', newText);
      window.location.hash = data.collapsed ? "": "details=open";
      $node.slideToggle('slow', 'easeOutQuad');
    }

    if (data.loaded) {
      hideShow();
    } else {
      $('body').spin();
      var url = l('/xhr/stats/checks/'),
          reqData = {
            path: this.pootlePath
          };
      $.ajax({
        url: url,
        data: reqData,
        success: function (data) {
          $node.hide();
          if (data !== null && Object.keys(data).length) {
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
        complete: onDataLoad
      });
    }
  },

  /* Re-open the path summary on page load if details=open present
     in location hash */
  reopenDetails: function () {
    var urlHash = window.location.hash.substring(1),
        details = urlHash.substr(urlhash.indexOf('details='))
                         .split('&')[0]
                         .split('=')[1];
    if (details === "open") {
      $('#js-path-summary').trigger('click');
    }
  },

  /* If details=open present in location hash append to href of
     clicked element */
  appendDetailsOpenHash: function (e) {
    var targetUrl = $(e.currentTarget).attr('href'),
        targetHash,
        urlHash = window.location.hash.substring(1),
        details = urlHash.substr(urlHash.indexOf('details='))
                         .split('&')[0]
                         .split('=')[1];

    if (details === 'open') {
      if (targetUrl.indexOf('#') === -1) {
        targetHash = '';
      } else {
        targetHash = targetUrl.substring(targetUrl.indexOf('#') + 1);
        targetUrl = targetUrl.substring(0, targetUrl.indexOf('#'));
      }

      if (targetHash === '') {
        targetHash = 'details=open';
      } else if (targetHash.indexOf('details=') === -1) {
        targetHash = targetHash + '&details=open';
      }
      targetUrl = targetUrl + '#' + targetHash;
    }
    $(e.currentTarget).attr('href', targetUrl);
    return true;
  }
};

module.exports = stats;
