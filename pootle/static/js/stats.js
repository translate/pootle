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

import 'jquery-utils';
import assign from 'object-assign';
import 'sorttable';

import LastUpdate from 'components/LastUpdate';
import TimeSince from 'components/TimeSince';
import UserEvent from 'components/UserEvent';
import cookie from 'utils/cookie';
import { q } from 'utils/dom';

import Stats from './browser/components/Stats';
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

    $(document).on('click', '#js-path-summary', (e) => {
      e.preventDefault();
      this.toggleDetailedStats();
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
    $(document).on('click', '.js-stats-refresh-close', (e) => {
      e.preventDefault();
      $('#autorefresh-notice').hide();
    });

    window.addEventListener('popstate', (e) => {
      const state = e.state;
      if (state) {
        this.setState({ isExpanded: state.isExpanded });
      }
    });

    if (this.isAdmin && options.hasDisabledItems) {
      ReactDOM.render(<VisibilityToggle uiLocaleDir={options.uiLocaleDir} />,
                      q('.js-mnt-visibility-toggle'));
    }

    ReactDOM.render(
      <Stats
        hasMoreContributors={options.topContributorsData.has_more_items}
        topContributors={options.topContributorsData.items}
        pootlePath={this.pootlePath}
      />,
      q('#js-mnt-top-contributors')
    );

    // Retrieve async data if needed
    if (!(isExpanded)) {
      this.updateUI();
    }
  },

  setState(newState) {
    this.state = assign({}, this.state, newState);
    this.updateUI();
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

  updateAction($action, count) {
    $action.toggleClass('non-zero', !(count === 0));
    $action.find('.counter').text(count !== null ? count : '—');
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
    const luWrapper = q('#js-last-updated-wrapper');
    const hideLastUpdated = !statsData.lastupdated || statsData.lastupdated.mtime === 0;
    luWrapper.classList.toggle('hide', hideLastUpdated);
    if (statsData.lastupdated) {
      const lastUpdated = q('#js-last-updated');
      this.renderLastUpdate(lastUpdated, statsData.lastupdated);
    }
    const laWrapper = q('#js-last-action-wrapper');
    const hideLastAction = !statsData.lastaction || statsData.lastaction.mtime === 0;
    laWrapper.classList.toggle('hide', hideLastAction);
    if (statsData.lastaction) {
      const lastAction = q('#js-last-action');
      this.renderLastEvent(lastAction, statsData.lastaction);
    }
  },

  updateStatsUI() {
    const { data } = this.state;

    const $table = $('#content table.stats');
    const $vfoldersTable = $('#content .vfolders table.stats');

    this.updateLastUpdates(data);

    if ($table.length) {
      if ($vfoldersTable.length) {
        for (const name in data.vfolders) {
          if (!data.vfolders.hasOwnProperty(name)) {
            continue;
          }

          const item = data.vfolders[name];
          const code = cssId(name);
          const $td = $vfoldersTable.find(`#total-words-${code}`);

          // Display only the virtual folders that must be displayed.
          if (!(this.isAdmin || item.isVisible)) {
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

  /* Path summary */
  toggleDetailedStats() {
    this.setState({ isExpanded: !this.state.isExpanded });
    this.navigate();
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
    const count = 0;

    if (data === null || !Object.keys(data).length) {
      return;
    }
    $('.js-more-checks').addClass('collapsed').toggle(count >= 5);
    $('#js-stats-checks').show();
  },

  updateUI() {
    this.updateChecksToggleUI();
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
