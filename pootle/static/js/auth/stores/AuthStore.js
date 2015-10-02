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

    this.registerAsync(authActions.verifySocial, this.handleVerifySocialBegin,
                                                 this.handleVerifySocialSuccess,
                                                 this.handleVerifySocialError);

    this.state = {
      redirectTo: null,

      // FIXME: check if isLoading is actually needed everywhere
      isLoading: false, // Should be part of some generic 'request' store?
      formErrors: {}, // Should be part of some generic 'error' store?
    };
  }


  /* Social Sign In Verification */

  handleVerifySocialBegin(reqData) {
    this.setState({
      formErrors: {},
      isLoading: true,
    });
  }

  handleVerifySocialSuccess(newLocation) {
    let newState = {
      isLoading: false,
      formErrors: {},
      redirectTo: newLocation,
    };

    this.setState(newState);
  }

  handleVerifySocialError(errors) {
    this.setState({
      isLoading: false,
      formErrors: errors,
    });
  }

}
