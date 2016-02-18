/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React from 'react';

import Textarea from './Textarea';
import { applyFontFilter, unapplyFontFilter } from '../utils';


const EditorTextarea = React.createClass({

  propTypes: {
    id: React.PropTypes.string,
    initialValue: React.PropTypes.string,
    isDisabled: React.PropTypes.bool,
    isRawMode: React.PropTypes.bool,
    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    onChange: React.PropTypes.func.isRequired,
    value: React.PropTypes.string,
    style: React.PropTypes.object,
  },

  getDefaultProps() {
    return {
      initialValue: '',
    };
  },

  getInitialState() {
    return {
      value: this.props.initialValue,
    };
  },

  getMode() {
    return this.props.isRawMode ? 'raw' : 'regular';
  },

  handleChange(e) {
    const newValue = e.target.value;
    const cleanValue = unapplyFontFilter(newValue, this.getMode());

    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    this.props.onChange(newValue);

    this.setState({
      value: cleanValue,
    });
  },

  render() {
    const transformedValue = applyFontFilter(this.state.value, this.getMode());
    const editorWrapperClasses = cx('editor-area-wrapper js-editor-area-wrapper', {
      'is-disabled': this.props.isDisabled,
    });

    return (
      <div className={editorWrapperClasses}>
        <Textarea
          id={this.props.id}
          initialValue={applyFontFilter(this.props.initialValue, this.getMode())}
          onChange={(e) => this.handleChange(e)}
          style={this.props.style}
          value={transformedValue}
        />
    </div>
    );
  },

});


export default EditorTextarea;
