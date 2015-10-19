/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import { PureRenderMixin } from 'react/addons';


let SocialSignInForm = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    socialAuthProviders: React.PropTypes.array.isRequired,
  },


  /* Handlers */

  handleClick(url) {
    let nextURL = window.location.pathname + window.location.hash;
    window.location = `${url}?next=${encodeURIComponent(nextURL)}`;
  },


  /* Layout */

  renderSocialAuthButton(socialAuth, index) {
    return (
      <button
        className="btn btn-big"
        key={index}
        onClick={this.handleClick.bind(null, socialAuth.url)}
      >
        {interpolate(gettext('Sign In With %s'), [socialAuth.name])}
      </button>
    );
  },

  render() {
    let signInWarningMsg = gettext('Signing in with an external service for the first time will automatically create an account for you.');

    return (
      <div className="actions sign-in-social">
        {this.props.socialAuthProviders.map(this.renderSocialAuthButton)}
        <p>{signInWarningMsg}</p>
      </div>
    );
  },

});


export default SocialSignInForm;
