/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React, { PropTypes } from 'react';
import { PureRenderMixin } from 'react-addons-pure-render-mixin';


const Avatar = React.createClass({

  // FIXME: be smarter with props validation, e.g. `email` should be required if
  // `src` is missing etc.
  propTypes: {
    emailHash: PropTypes.string,
    label: PropTypes.string,
    size: PropTypes.number,
    src: PropTypes.string,
    title: PropTypes.string,
    username: PropTypes.string,
  },

  mixins: [PureRenderMixin],

  getDefaultProps() {
    return {
      size: 80,
    };
  },

  render() {
    const { emailHash } = this.props;
    const { label } = this.props;
    const { size } = this.props;
    const { title } = this.props;
    const { username } = this.props;

    const imgSrc = `https://secure.gravatar.com/avatar/${emailHash}?s=${size}&d=mm`;

    const icon = (
      <img
        className="avatar"
        src={imgSrc}
        height={size}
        width={size}
        title={title}
      />
    );

    if (username !== undefined) {
      return (
        <a href={l(`/user/${username}/`)}>
          {icon}
          {label && ' '}
          {label &&
            <span className="user-name" title={username}>{label}</span>
          }
        </a>
      );
    }

    return icon;
  },

});


export default Avatar;
