/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import fetch from 'utils/fetch';

window.PTL = window.PTL || {};

const UnitAPI = {

  apiRoot: PTL.unitApiRoot,

  fetchUnits(body) {
    return fetch({
      body,
      url: this.apiRoot,
    });
  },

  fetchUnit(uId, body = {}) {
    return fetch({
      body,
      queue: 'unitWidget',
      url: `${this.apiRoot}${uId}/edit/`,
    });
  },

  addTranslation(uId, body) {
    return fetch({
      body,
      method: 'POST',
      url: `${this.apiRoot}${uId}`,
    });
  },

  getContext(uId, body) {
    return fetch({
      body,
      url: `${this.apiRoot}${uId}/context/`,
    });
  },

  getTimeline(uId) {
    return fetch({
      url: `${this.apiRoot}${uId}/timeline/`,
    });
  },

  addComment(uId, body) {
    return fetch({
      body,
      method: 'POST',
      url: `${this.apiRoot}${uId}/comment/`,
    });
  },

  removeComment(uId) {
    return fetch({
      method: 'DELETE',
      url: `${this.apiRoot}${uId}/comment/`,
    });
  },

  /* Unit suggestions */

  addSuggestion(uId, body) {
    return fetch({
      body,
      method: 'POST',
      url: `${this.apiRoot}${uId}/suggestions/`,
    });
  },

  acceptSuggestion(uId, suggId, body) {
    return fetch({
      body,
      method: 'POST',
      url: `${this.apiRoot}${uId}/suggestions/${suggId}/`,
    });
  },

  rejectSuggestion(uId, suggId, body) {
    return fetch({
      body,
      method: 'DELETE',
      url: `${this.apiRoot}${uId}/suggestions/${suggId}/`,
    });
  },

  /* Quality checks */

  toggleCheck(uId, checkId, body = {}) {
    return fetch({
      body,
      method: 'POST',
      url: `${this.apiRoot}${uId}/checks/${checkId}/toggle/`,
    });
  },

};


export default UnitAPI;
