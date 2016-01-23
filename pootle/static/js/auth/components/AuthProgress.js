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


const AuthProgress = React.createClass({

  propTypes: {
    msg: React.PropTypes.string.isRequired,
  },

  mixins: [PureRenderMixin],

  render() {
    const msgStyle = {
      textAlign: 'center',
    };
    return (
      <AuthContent>
        <p style={msgStyle}>{this.props.msg}</p>
      </AuthContent>
    );
  },

});


export default AuthProgress;
