/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import Backbone from 'backbone';

import { Unit } from './models';


/*
 * collections.UnitSet
 */

export const UnitSet = Backbone.Collection.extend({
  model: Unit,

  initialize(model, opts) {
    this.chunkSize = opts.chunkSize;
    this.uIds = [];
    this.total = 0;
    this.frozenTotal = 0;
  },

  comparator(unit) {
    return this.uIds.indexOf(unit.id);
  },

  getByUnitId(uId) {
    return uId > 0 ? this.get(uId) : this.at(0);
  },

  getCurrent() {
    return this.activeUnit;
  },
  setCurrent(unit) {
    this.activeUnit = unit instanceof this.model ? unit : this.getByUnitId(unit);
    return this.activeUnit;
  },

  fetchedIds() {
    return this.map((unit) => unit.id);
  },

  next() {
    const index = this.indexOf(this.getCurrent());
    return (index + 1 === this.length) ? null : this.at(index + 1);
  },

  hasNext() {
    return this.next() !== null;
  },

  prev() {
    const index = this.indexOf(this.getCurrent());
    return (index === 0) ? null : this.at(index - 1);
  },

  hasPrev() {
    return this.prev() !== null;
  },

});
