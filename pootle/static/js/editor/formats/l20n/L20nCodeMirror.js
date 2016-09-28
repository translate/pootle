/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import CodeMirror from '../../../shared/components/CodeMirror';


const L20nCodeMirror = React.createClass({
  displayName: 'L20nCodeMirror',

  render() {
    return (
      <CodeMirror
        markup="javascript"
        {...this.state}
        {...this.props}
      />
    );
  },
});


export default L20nCodeMirror;
