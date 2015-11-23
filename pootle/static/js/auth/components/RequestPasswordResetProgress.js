/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import { PureRenderMixin } from 'react/addons';

import AuthProgress from './AuthProgress';


const RequestPasswordResetProgress = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    email: React.PropTypes.string.isRequired,
  },

  render() {
      let sendingMsg = interpolate(gettext('Sending email to %s...'),
                                   [this.props.email]);
      return <AuthProgress msg={sendingMsg} />;
  },

});


export default RequestPasswordResetProgress;
