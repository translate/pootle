/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import Backbone from 'backbone';


const sel = {
  data: {
    toggle: '[data-action="toggle"]',
  },
  target: '.dropdown-menu',
  targetItems: 'li:not(.menu-divider) a',
  open: 'show-dropdown',
};

const keys = {
  ESC: 27,
  UP: 38,
  DOWN: 40,
};


const DropdownView = Backbone.View.extend({

  events() {
    const events = {
      keydown: 'onKey',
    };
    events[`click ${sel.data.toggle}`] = 'toggle';

    return events;
  },

  initialize() {
    this.$toggle = this.$(sel.data.toggle);
    this.$target = this.$(sel.target);

    this.$target.css('width', this.$el.width());

    $(document).on('click.PTL.dropdown', this.hide.bind(this));
  },

  onKey(e) {
    // Avoid hijacking browser keyboard shortcuts when not shown
    if (!this.isVisible()) {
      return true;
    }

    if ([keys.ESC, keys.UP, keys.DOWN].indexOf(e.which) !== -1) {
      e.preventDefault();
    }

    if (e.which === keys.ESC) {
      return this.$toggle.click();
    }

    if ([keys.UP, keys.DOWN].indexOf(e.which) !== -1) {
      const $items = this.$target.find(sel.targetItems);

      if (!$items.length) {
        return false;
      }

      let index = $items.index($items.filter(':focus'));

      if (e.which === keys.UP && index > 0) {
        index--;
      }
      if (e.which === keys.DOWN && index < $items.length - 1) {
        index++;
      }
      if (!index) {
        index = 0;
      }

      $items.eq(index).trigger('focus');
    }

    return true;
  },

  isVisible() {
    return this.$el.hasClass(sel.open);
  },

  show() {
    if (!this.isVisible()) {
      this.$el.addClass(sel.open);
    }
  },

  hide() {
    if (this.isVisible()) {
      this.$el.removeClass(sel.open);
    }
  },

  toggle(e) {
    e.preventDefault();
    e.stopPropagation();

    this.$el.toggleClass(sel.open);

    if (this.isVisible()) {
      this.$toggle.focus();
    } else {
      this.$toggle.blur();
    }
  },

});


const dropdown = {

  init(el) {
    return new DropdownView({ el: el instanceof $ ? el : $(el) });
  },

};


export default dropdown;
