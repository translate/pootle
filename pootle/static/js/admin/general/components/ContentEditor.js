/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import CodeMirror from 'components/CodeMirror';
import { getName } from 'utils/markup';


const ContentEditor = React.createClass({

  propTypes: {
    markup: React.PropTypes.string,
    // Temporarily needed to support submitting forms not controlled by JS
    name: React.PropTypes.string,
    onChange: React.PropTypes.func,
    style: React.PropTypes.object,
    value: React.PropTypes.string,
  },

  render() {
    const { markup } = this.props;
    const markupName = getName(markup);

    return (
      <div
        className="content-editor"
        style={this.props.style}
      >
        <CodeMirror
          markup={markup}
          name={this.props.name}
          value={this.props.value}
          onChange={this.props.onChange}
          placeholder={gettext(`Allowed markup: ${markupName}`)}
        />
      </div>
    );
  },

});


export default ContentEditor;
