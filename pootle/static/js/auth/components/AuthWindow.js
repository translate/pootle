/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import Modal from 'components/Modal';


const AuthWindow = React.createClass({
  propTypes: {
    canContact: React.PropTypes.bool.isRequired,
  },


  renderFooter() {
    if (!this.props.canContact) {
      return null;
    }

    return (
      <a href="#" className="js-contact">
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
  },

});


export default AuthWindow;
