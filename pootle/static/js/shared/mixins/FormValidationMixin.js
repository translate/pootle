/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';  // eslint-disable-line no-unused-vars


export const FormValidationMixin = {

  getInitialState() {
    return {
      errors: {},
    };
  },

  clearValidation() {
    this.setState({ errors: {} });
  },

  validateResponse(xhr) {
    // XXX: should this also check for HTTP 500, 404 etc.?
    const response = JSON.parse(xhr.responseText);
    this.setState({ errors: response.errors });
  },


  /* Layout */

  renderSingleError(errorMsg, i) {
    return <li key={i}>{errorMsg}</li>;
  },


  /* Renders form's global errors. These errors come in a special
   * `__all__` field */
  renderAllFormErrors() {
    const { errors } = this.state;

    if (errors.hasOwnProperty('__all__')) {
      return (
        <ul className="errorlist errorlist-all">
          {errors.__all__.map(this.renderSingleError)}
        </ul>
      );
    }

    return null;
  },

};


export default FormValidationMixin;
