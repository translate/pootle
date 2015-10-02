/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import { Store } from 'flummox';
import assign from 'object-assign';


export default class AuthStore extends Store {

  constructor(flux) {
    super();

    let authActions = flux.getActions('auth');

    this.state = {};
  }

}
