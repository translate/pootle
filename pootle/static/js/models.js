/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import Backbone from 'backbone';
import _ from 'underscore';


/*
 * Unit
 */

export const Unit = Backbone.Model.extend({

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
