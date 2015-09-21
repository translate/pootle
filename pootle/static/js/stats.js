/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import React from 'react';

import 'jquery-bidi';
import 'jquery-utils';
import assign from 'object-assign';
import 'sorttable';

import LastUpdate from 'components/LastUpdate';
import TimeSince from 'components/TimeSince';
import UserEvent from 'components/UserEvent';
import helpers from './helpers';


const nicePercentage = function (part, total, noTotalDefault) {
  const percentage = total ? part / total * 100 : noTotalDefault;
  if (99 < percentage && percentage < 100) {
    return 99;
  }
  if (0 < percentage && percentage < 1) {
    return 1;
  }
  return Math.round(percentage);
};


function cssId(id) {
  return id.replace(/[\.@\+\s]/g, '-');
}


const stats = {

  init(options) {
    this.retries = 0;

    const isExpanded = (options.isInitiallyExpanded ||
                        window.location.search.indexOf('?details') !== -1);
    this.state = {
      isExpanded: isExpanded,
      checksData: null,
      data: options.initialData,
    };

    this.pootlePath = options.pootlePath;
    this.isAdmin = options.isAdmin;

    this.$extraDetails = $('#js-path-summary-more');
    this.$expandIcon = $('#js-expand-icon');

    $('td.stats-name').filter(':not([dir])').bidi();

    $(document).on('click', '#js-path-summary', (e) => {
      e.preventDefault();
      this.toggleChecks();
    });
    $(document).on('click', '.js-stats-refresh', (e) => {
      e.preventDefault();
      this.refreshStats();
    });

    window.addEventListener('popstate', (e) => {
      const state = e.state;
      if (state) {
        this.setState({isExpanded: state.isExpanded});
      }
    });

    // Retrieve async data if needed
    if (isExpanded) {
      this.loadChecks();
    } else {
      this.updateUI({});
    }
  },

  setState(newState) {
    this.state = assign({}, this.state, newState);
    this.updateUI();
  },

  refreshStats() {
    this.dirtyBackoff = 1;
    this.updateDirty();
  },

  updateProgressbar($td, item) {
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

  updateTranslationStats($tr, total, value, noTotalDefault) {
    $tr.find('.stats-number a').html(value);
    $tr.find('.stats-percentage span').html(
      nicePercentage(value, total, noTotalDefault)
    );
    $tr.find('.stats-percentage').show();
  },

  updateAction($action, count) {
    $action.toggleClass('non-zero', !(count === 0));
    $action.find('.counter').text(count !== null ? count : '—');
  },

  updateItemStats($td, count) {
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

  renderLastEvent(el, data) {
    if (data.mtime === 0) {
      return false;
    }

    const props = {
      checkName: data.check_name,
      checkDisplayName: data.check_display_name,
      displayName: data.displayname,
      email: data.email,
      displayDatetime: data.display_datetime,
      isoDatetime: data.iso_datetime,
      type: data.type,
      translationActionType: data.translation_action_type,
      unitSource: data.unit_source,
      unitUrl: data.unit_url,
      username: data.username,
    };
    React.render(<UserEvent {...props} />, el);
  },

  renderLastUpdate(el, data) {
    if (data.creation_time === 0) {
      return false;
    }

    const props = {
      displayDatetime: data.display_datetime,
      isoDatetime: data.iso_datetime,
      unitSource: data.unit_source,
      unitUrl: data.unit_url,
    };
    React.render(<LastUpdate {...props} />, el);
  },

  renderLastUpdatedTime(el, data) {
    if (data.creation_time === 0) {
      return false;
    }

    const props = {
      title: data.display_datetime,
      dateTime: data.iso_datetime,
    };
    React.render(<TimeSince {...props} />, el);
  },

  updateLastUpdates(stats) {
    if (stats.lastupdated) {
      const lastUpdated = document.querySelector('#js-last-updated .last-updated');
      this.renderLastUpdate(lastUpdated, stats.lastupdated);
    }
    if (stats.lastaction) {
      const lastAction = document.querySelector('#js-last-action .last-action');
      this.renderLastEvent(lastAction, stats.lastaction);
    }
  },

  processTableItem(item, code, $table, $td, now) {
    if (!$td.length) {
      return null;
    }

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
      this.renderLastEvent($td[0], item.lastaction);
      $td.attr('sorttable_customkey', now - item.lastaction.mtime);
    }

    $td = $table.find('#critical-' + code);
    this.updateItemStats($td, item.critical);

    if (item.lastupdated) {
      $td = $table.find('#last-updated-' + code);
      $td.removeClass('not-inited');
      this.renderLastUpdatedTime($td[0], item.lastupdated);
      $td.attr('sorttable_customkey', now - item.lastupdated.creation_time);
    }
  },

  updateStatsUI() {
    const { data } = this.state;

    var $table = $('#content table.stats'),
        $vfoldersTable = $('#content .vfolders table.stats'),
        dirtySelector = '#top-stats, #translate-actions, #autorefresh-notice',
        now = parseInt(Date.now() / 1000, 10);

    $(dirtySelector).toggleClass('dirty', !!data.is_dirty);
    if (!!data.is_dirty) {
      this.dirtyBackoff = Math.pow(2, this.retries);
      this.updateDirtyBackoffCounter();
      $('.js-stats-refresh').show();
      this.dirtyBackoffId = setInterval(() => this.updateDirty(), 1000);
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
    }

  },

  updateDirty() {
    if (--this.dirtyBackoff === 0) {
      $('.js-stats-refresh').hide();
      clearInterval(this.dirtyBackoffId);
      setTimeout(() => {
        if (this.retries < 5) {
          this.retries++;
        }
        this.loadStats();
      }, 250);
    }
    this.updateDirtyBackoffCounter();
  },

  updateDirtyBackoffCounter() {
    var noticeStr = ngettext('%s second', '%s seconds', this.dirtyBackoff);
    noticeStr = interpolate(noticeStr, [this.dirtyBackoff], false);
    $('#autorefresh-notice strong').text(noticeStr);
  },

  load(url, data) {
    $('body').spin();
    return (
      $.ajax({
        url,
        data,
        dataType: 'json',
      }).always(() => $('body').spin(false))
    );
  },

  loadStats() {
    return (
      this.load(l('/xhr/stats/'), {path: this.pootlePath})
          .done((data) => this.setState({data}))
    );
  },

  loadChecks() {
    return (
      this.load(l('/xhr/stats/checks'), {path: this.pootlePath})
          .done((data) => this.setState({isExpanded: true, checksData: data}))
    );
  },

  /* Path summary */
  toggleChecks() {
    if (this.state.checksData) {
      this.setState({isExpanded: !this.state.isExpanded});
      this.navigate();
    } else {
      this.loadChecks().done(() => this.navigate());
    }
  },

  updateChecksToggleUI() {
    const { isExpanded } = this.state;

    const newClass = isExpanded ? 'collapse' : 'expand';
    const newText = isExpanded ? gettext('Collapse details') : gettext('Expand details');

    this.$expandIcon.attr('class', `icon-${newClass}-stats`);
    this.$expandIcon.attr('title', newText);

    this.$extraDetails.toggle(isExpanded);
  },

  updateChecksUI() {
    const data = this.state.checksData;

    if (data !== null && Object.keys(data).length) {
      this.$extraDetails.find('.js-checks').each(function (e) {
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
  },

  updateUI() {
    this.updateChecksToggleUI();
    this.updateChecksUI();
    this.updateStatsUI();
  },

  navigate() {
    const { isExpanded } = this.state;
    const currentURL = `${window.location.pathname}${window.location.search}`;
    const path = l(this.pootlePath);
    const newURL = isExpanded ? `${path}?details` : path;
    if (currentURL !== newURL) {
      window.history.pushState({isExpanded}, '', newURL);
    }
  },

};


export default stats;
