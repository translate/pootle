/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import { PureRenderMixin } from 'react/addons';


const AuthContent = React.createClass({
  mixins: [PureRenderMixin],

  render() {
    // FIXME: use flexbox when possible
    let style = {
      outer: {
        display: 'table',
        height: '22em',
        width: '100%',
      },
      inner: {
        display: 'table-cell',
        verticalAlign: 'middle',
      },
    };

    return (
      <div style={style.outer}>
        <div style={style.inner}>
          {this.props.children}
        </div>
      </div>
    );
  },

});


export default AuthContent;
