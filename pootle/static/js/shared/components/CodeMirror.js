/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import * as CM from 'codemirror';
import 'codemirror/addon/display/placeholder';
import 'codemirror/lib/codemirror.css';

import { getMode } from 'utils/markup';

import './CodeMirror.css';


const CodeMirror = React.createClass({

  propTypes: {
    markup: React.PropTypes.string,
    // Temporarily needed to support submitting forms not controlled by JS
    name: React.PropTypes.string,
    onChange: React.PropTypes.func,
    placeholder: React.PropTypes.string,
    value: React.PropTypes.string,
  },

  getDefaultProps() {
    return {
      markup: 'html',
    };
  },

  componentDidMount() {
    const mode = getMode(this.props.markup);

    // Using webpack's `bundle` loader so each mode goes into a separate chunk
    const bundledResult = require(`bundle!codemirror/mode/${mode}/${mode}.js`);
    bundledResult(() => {
      this.codemirror = CM.fromTextArea(this.refs.editor, {
        mode,
        lineWrapping: true,
      });

      this.codemirror.on('change', this.handleChange);
    });
  },

  handleChange() {
    if (this.props.onChange) {
      this.props.onChange(this.codemirror.getValue());
    }
  },

  render() {
    const extraProps = {};

    if (this.props.name) {
      extraProps.name = this.props.name;
    }

    return (
      <textarea
        defaultValue={this.props.value}
        placeholder={this.props.placeholder}
        ref="editor"
        {...extraProps}
      />
    );
  },

});


export default CodeMirror;
