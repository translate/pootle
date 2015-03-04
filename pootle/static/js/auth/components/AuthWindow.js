/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import React from 'react';

import { Modal } from 'components/lightbox';


let AuthWindow = React.createClass({

  renderFooter() {
    return (
      <a href={l('/contact/')} className="js-popup-ajax">
        {gettext('Contact Us')}
      </a>
    );
  },

  render() {
    return (
      <Modal
        className="auth-window"
        footer={this.renderFooter}
        {...this.props}
      />
    );
  }

});


export default AuthWindow;
