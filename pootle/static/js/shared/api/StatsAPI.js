/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import fetch from 'utils/fetch';


const StatsAPI = {

  apiRoot: '/xhr/stats/',

  getTopContributors(path, { offset = 0 } = {}) {
    const body = { path, offset };

    return fetch({
      body,
      url: `${this.apiRoot}contributors/`,
    });
  },

};


export default StatsAPI;
