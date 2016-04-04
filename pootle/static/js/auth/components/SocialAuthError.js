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


const SocialAuthError = React.createClass({

  propTypes: {
    socialError: React.PropTypes.object,
  },

  mixins: [PureRenderMixin],

  /* Layout */

  render() {
    const { socialError } = this.props;
    let errorMsg;
    if (socialError) {
      errorMsg = interpolate(
        gettext('An error occurred while attempting to sign in via %s.'),
        [socialError.provider]
      );
    } else {
      errorMsg = gettext(
        'An error occurred while attempting to sign in via your social account.'
      );
    }

    const errorFace = {
      fontSize: '400%',
      marginBottom: '0.5em',
    };
    return (
      <AuthContent style={{ textAlign: 'center' }}>
        <h2 style={errorFace}>{'{õ_õ}'}</h2>
        <p>{errorMsg}</p>
      {socialError &&
        <p>{`${socialError.exception.name}: ${socialError.exception.msg} `}</p>
      }
      {socialError &&
        <a href={socialError.retry_url}>
          {gettext('Try again')}
        </a>
      }
      </AuthContent>
    );
  },

});


export default SocialAuthError;
