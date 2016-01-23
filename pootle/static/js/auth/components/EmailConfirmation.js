/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import { PureRenderMixin } from 'react-addons-pure-render-mixin';

import AuthContent from './AuthContent';


const EmailConfirmation = React.createClass({

  propTypes: {
    onClose: React.PropTypes.func.isRequired,
  },

  mixins: [PureRenderMixin],

  /* Layout */

  render() {
    return (
      <AuthContent>
        <p>{gettext('This email confirmation link expired or is invalid.')}</p>
        <div className="actions">
          <button
            className="btn btn-primary"
            onClick={this.props.onClose}
          >
            {gettext('Close')}
          </button>
        </div>
      </AuthContent>
    );
  },

});


export default EmailConfirmation;
