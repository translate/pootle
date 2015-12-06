/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import _ from 'underscore';


const AdminAPIMixin = {

  initialize() {
    this.count = 0;
    this.page = 0;
    this.keywords = '';

    this.on('add', this.incrCount);
    this.on('remove', this.decrCount);
  },

  parse(response) {
    this.count = response.count;

    return response.models;
  },

  comparator: '-id',


  /* Methods */

  incrCount() {
    this.count++;
  },

  decrCount() {
    this.count--;
  },

  fetchNextPage(opts) {
    const newPage = this.page + 1;
    const pageData = newPage === 1 ? {} : { p: newPage };
    const keywordsData = this.keywords === '' ? {} : { q: this.keywords };
    const reqData = _.extend({}, pageData, keywordsData);

    const fetchOpts = { remove: false, silent: true, data: reqData };
    _.defaults(fetchOpts, opts);

    return this.fetch(fetchOpts).done(() => {
      this.page = newPage;
    });
  },

  search(keywords) {
    const opts = {};
    if (keywords !== this.keywords) {
      this.setSearch(keywords);
      opts.reset = true;
    }
    return this.fetchNextPage(opts);
  },

  setSearch(keywords) {
    this.keywords = keywords;
    this.page = 0;
  },

};


export default AdminAPIMixin;
