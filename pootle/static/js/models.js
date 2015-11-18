/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import Backbone from 'backbone';
import 'backbone-relational';
import _ from 'underscore';


/*
 * Store
 */

export const Store = Backbone.RelationalModel.extend({});


/*
 * Unit
 */

export const Unit = Backbone.RelationalModel.extend({

  relations: [{
    type: 'HasOne',
    key: 'store',
    relatedModel: Store,
    reverseRelation: {
      key: 'units',
    },
  }],

  /*
   * Sets the current unit's translation.
   */
  setTranslation(value) {
    let newValue = value;
    if (!_.isArray(value)) {
      newValue = [value];
    }
    this.set('target', newValue);
  },

});
