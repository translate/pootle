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

import cookie from 'utils/cookie';
import { q } from 'utils/dom';

import Stats from './browser/components/Stats';
import VisibilityToggle from './browser/components/VisibilityToggle';
import msg from './msg';


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
    this.$extraDetails = $('#js-path-summary-more');
    this.$expandIcon = $('#js-expand-icon');

    $(document).on('click', '#js-path-summary', (e) => {
      e.preventDefault();
      this.toggleDetailedStats();
    });
    $(document).on('click', '.js-toggle-more-checks', (e) => {
      let count = 0;
      e.preventDefault();
      $('.js-check').each(function toggleCheck() {
        const $check = $(this);
        if (count >= 4) {
          $check.toggle();
        }
        count++;
      });
      $(e.target).parent().toggleClass('collapsed');
    });

    window.addEventListener('popstate', (e) => {
      const state = e.state;
      if (state) {
        this.setState({ isExpanded: state.isExpanded });
      }
    });

    if (options.hasDisabledItems) {
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
    this.updateUI();
    this.updateStatsUI();
  },

  setState(newState) {
    this.state = assign({}, this.state, newState);
    this.updateUI();
    this.updateChecksToggleUI();
  },

  updateStatsUI() {
    const $table = $('#content table.stats');

    if ($table.length) {
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
    if (!(this.state.checksData)) {
      this.setState({ isExpanded: !this.state.isExpanded });
    }
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
    let count = 0;

    this.$extraDetails.find('.js-check').each(function updateCheck() {
      const $check = $(this);
      count++;
      $check.toggle(count < 5);
    });

    $('.js-more-checks').addClass('collapsed').toggle(count >= 5);
    $('#js-stats-checks').show();
  },

  updateUI() {
    this.updateChecksToggleUI();
    this.updateChecksUI();
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
