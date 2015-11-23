/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import { PureRenderMixin } from 'react/addons';

import AuthContent from './AuthContent';


const SocialAuthError = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    socialError: React.PropTypes.object,
  },


  /* Layout */

  render() {
    let errorMsg;
    if (this.props.socialError) {
      errorMsg = interpolate(
        gettext('An error occurred while attempting to sign in via %s.'),
        [this.props.socialError.provider]
      );
    } else {
      errorMsg = gettext('An error occurred while attempting to sign in via your social account.');
    }

    let errorFace = {
      fontSize: '400%',
      marginBottom: '0.5em',
    };
    return (
      <AuthContent>
        <h2 style={errorFace}>{`{õ_õ}`}</h2>
        <p>{errorMsg}</p>
      {this.props.socialError &&
        <p>{`${this.props.socialError.exception.name}: ${this.props.socialError.exception.msg} `}</p>
      }
      {this.props.socialError &&
        <a href={this.props.socialError.retry_url}>
          {gettext('Try again')}
        </a>
      }
      </AuthContent>
    );
  },

});


export default SocialAuthError;
