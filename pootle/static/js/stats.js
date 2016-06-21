/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import React from 'react';
import ReactDOM from 'react-dom';

import 'jquery-bidi';
import 'jquery-utils';
import assign from 'object-assign';
import 'sorttable';

import StatsAPI from 'api/StatsAPI';
import LastUpdate from 'components/LastUpdate';
import TimeSince from 'components/TimeSince';
import UserEvent from 'components/UserEvent';
import cookie from 'utils/cookie';

import VisibilityToggle from './browser/components/VisibilityToggle';
import msg from './msg';


function nicePercentage(part, total, noTotalDefault) {
  const percentage = total ? part / total * 100 : noTotalDefault;
  if (percentage > 99 && percentage < 100) {
    return 99;
  }
  if (percentage > 0 && percentage < 1) {
    return 1;
  }
  return Math.round(percentage);
}


function cssId(id) {
  return id.replace(/[\.@\+\s]/g, '-');
}


function setTdWidth($td, w) {
  if (w === 0) {
    $td.hide();
  } else {
    $td.css('width', `${w}%`).show();
  }
}


const stats = {

  init(options) {
    if (cookie('finished')) {
      msg.show({
        text: gettext('Congratulations! You have completed this task!'),
        level: 'success',
      });
      cookie('finished', null, { path: '/' });
    }

    this.retries = 0;

    const isExpanded = (options.isInitiallyExpanded ||
                        window.location.search.indexOf('?details') !== -1);
    this.state = {
      isExpanded,
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
    $(document).on('click', '.js-toggle-more-checks', (e) => {
      let count = 0;
      const data = this.state.checksData;
      e.preventDefault();
      $('.js-check').each(function toggleCheck() {
        const $check = $(this);
        const code = $check.data('code');
        if (code in data) {
          if (count >= 4) {
            $check.toggle();
          }
          count++;
        }
      });
      $(e.target).parent().toggleClass('collapsed');
    });
    $(document).on('click', '.js-stats-refresh', (e) => {
      e.preventDefault();
      this.refreshStats();
    });

    window.addEventListener('popstate', (e) => {
      const state = e.state;
      if (state) {
        this.setState({ isExpanded: state.isExpanded });
      }
    });

    if (this.isAdmin && options.hasDisabledItems) {
      ReactDOM.render(<VisibilityToggle uiLocaleDir={options.uiLocaleDir} />,
                      document.querySelector('.js-mnt-visibility-toggle'));
    }

    // Retrieve async data if needed
    if (isExpanded) {
      this.loadChecks();
    } else {
      this.updateUI();
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
    const translated = nicePercentage(item.translated, item.total, 100);
    const fuzzy = nicePercentage(item.fuzzy, item.total, 0);
    const untranslatedCount = 100 - translated - fuzzy;
    const untranslated = untranslatedCount < 0 ? 0 : untranslatedCount;
    const $legend = $('<span>').html($td.find('script').text());

    $legend.find('.value.translated').text(translated);
    $legend.find('.value.fuzzy').text(fuzzy);
    $legend.find('.value.untranslated').text(untranslated);

    $td.find('table').attr('title', $legend.html());

    setTdWidth($td.find('td.translated'), translated);
    setTdWidth($td.find('td.fuzzy'), fuzzy);
    setTdWidth($td.find('td.untranslated'), untranslated);
  },

  updateTranslationStats($tr, total, value, noTotalDefault) {
    $tr.find('.stats-number .stats-data').html(value);
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
      $td.find('.stats-data').html(count);
    } else if (count === 0) {
      $td.find('.stats-data').html('');
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
    ReactDOM.render(<UserEvent {...props} />, el);
    return true;
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
    ReactDOM.render(<LastUpdate {...props} />, el);
    return true;
  },

  renderLastUpdatedTime(el, data) {
    if (data.creation_time === 0) {
      return false;
    }

    const props = {
      title: data.display_datetime,
      dateTime: data.iso_datetime,
    };
    ReactDOM.render(<TimeSince {...props} />, el);
    return true;
  },

  updateLastUpdates(statsData) {
    const luWrapper = document.querySelector('#js-last-updated-wrapper');
    const hideLastUpdated = !statsData.lastupdated || statsData.lastupdated.mtime === 0;
    luWrapper.classList.toggle('hide', hideLastUpdated);
    if (statsData.lastupdated) {
      const lastUpdated = document.querySelector('#js-last-updated');
      this.renderLastUpdate(lastUpdated, statsData.lastupdated);
    }
    const laWrapper = document.querySelector('#js-last-action-wrapper');
    const hideLastAction = !statsData.lastaction || statsData.lastaction.mtime === 0;
    laWrapper.classList.toggle('hide', hideLastAction);
    if (statsData.lastaction) {
      const lastAction = document.querySelector('#js-last-action');
      this.renderLastEvent(lastAction, statsData.lastaction);
    }
  },

  processTableItem(item, code, $table, $tdEl, now) {
    let $td = $tdEl;
    if (!$td.length) {
      return false;
    }

    $td.parent().toggleClass('dirty', item.is_dirty);
    this.updateItemStats($td, item.total);

    const isFullRatio = item.total === 0 || item.total === null;
    const ratio = isFullRatio ? 1 : item.translated / item.total;
    $table.find(`#translated-ratio-${code}`).text(ratio);

    $td = $table.find(`#need-translation-${code}`);
    const needTranslationCount = (item.total !== null ?
                                  item.total - item.translated :
                                  null);
    this.updateItemStats($td, needTranslationCount);

    $td = $table.find(`#suggestions-${code}`);
    this.updateItemStats($td, item.suggestions);

    $td = $table.find(`#progressbar-${code}`);
    this.updateProgressbar($td, item);

    if (item.lastaction) {
      $td = $table.find(`#last-activity-${code}`);
      $td.removeClass('not-inited');
      this.renderLastEvent($td[0], item.lastaction);
      $td.attr('sorttable_customkey', now - item.lastaction.mtime);
    }

    $td = $table.find(`#critical-${code}`);
    this.updateItemStats($td, item.critical);

    if (item.lastupdated) {
      $td = $table.find(`#last-updated-${code}`);
      $td.removeClass('not-inited');
      this.renderLastUpdatedTime($td[0], item.lastupdated);
      $td.attr('sorttable_customkey', now - item.lastupdated.creation_time);
    }
    return true;
  },

  updateStatsUI() {
    const { data } = this.state;

    const $table = $('#content table.stats');
    const $vfoldersTable = $('#content .vfolders table.stats');
    const dirtySelector = '#top-stats, #translate-actions, #autorefresh-notice';
    const now = parseInt(Date.now() / 1000, 10);

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

    const untranslated = (data.total === null ?
                          null :
                          data.total - data.translated - data.fuzzy);
    this.updateTranslationStats($('#stats-untranslated'),
                                data.total, untranslated, 0);
    this.updateLastUpdates(data);

    if ($table.length) {
      // this is a directory that contains subitems
      for (const name in data.children) {
        if (!data.children.hasOwnProperty(name)) {
          continue;
        }

        const item = data.children[name];
        const code = cssId(name);
        const $td = $table.find(`#total-words-${code}`);

        this.processTableItem(item, code, $table, $td, now);
      }

      if ($vfoldersTable.length) {
        for (const name in data.vfolders) {
          if (!data.vfolders.hasOwnProperty(name)) {
            continue;
          }

          const item = data.vfolders[name];
          const code = cssId(name);
          const $td = $vfoldersTable.find(`#total-words-${code}`);

          // Display only the virtual folders that must be displayed.
          if (this.isAdmin || item.isVisible) {
            this.processTableItem(item, code, $vfoldersTable, $td, now);
          } else {
            // FIXME vfolders might be added or removed since they can become
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
      const columnSort = sorttable.getSortCookie($table.data('sort-cookie'));
      if (columnSort !== null) {
        const $th = $(`#${columnSort.columnId}`);
        $th.removeClass('sorttable_sorted sorttable_sorted_reverse');
        setTimeout(() => {
          $th.click();
          if (columnSort.order === 'desc') {
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
    const noticeStr = interpolate(
      ngettext('%s second', '%s seconds', this.dirtyBackoff),
      [this.dirtyBackoff],
      false
    );
    $('#autorefresh-notice strong').text(noticeStr);
  },

  load(methodName) {
    $('body').spin();
    return StatsAPI[methodName](this.pootlePath)
      .always(() => $('body').spin(false));
  },

  loadStats() {
    return this.load('getStats')
      .done((data) => this.setState({ data }));
  },

  loadChecks() {
    return this.load('getChecks')
      .done((data) => this.setState({ isExpanded: true, checksData: data }));
  },

  /* Path summary */
  toggleChecks() {
    if (this.state.checksData) {
      this.setState({ isExpanded: !this.state.isExpanded });
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

    this.$extraDetails.toggleClass('expand', isExpanded);
  },

  updateChecksUI() {
    const data = this.state.checksData;
    let count = 0;

    if (data === null || !Object.keys(data).length) {
      return;
    }

    this.$extraDetails.find('.js-check').each(function updateCheck() {
      const $check = $(this);
      const code = $(this).data('code');
      if (code in data) {
        count++;
        $check.toggle(count < 5);
        $check.find('.check-count .check-data').html(data[code]);
      } else {
        $check.hide();
      }
    });

    $('.js-more-checks').addClass('collapsed').toggle(count >= 5);
    $('#js-stats-checks').show();
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
      window.history.pushState({ isExpanded }, '', newURL);
    }
  },

};


export default stats;
