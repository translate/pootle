/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React from 'react';

import { applyFontFilter, unapplyFontFilter, isNewlineSymbol } from '../utils';


const NO_OVERWRITE_KEYS = [
  'Tab', 'PageUp', 'PageDown', 'Home', 'End', 'Insert', 'Escape',
  'ScrollLock', 'NumLock',
];


function shouldEventOverwriteSelection(e) {
  const { key } = e;
  return (
    !e.getModifierState(key) &&
    !e.altKey && !e.ctrlKey && !e.shiftKey && !e.metaKey &&
    NO_OVERWRITE_KEYS.indexOf(key) === -1 &&
    key.search(/^Arrow[a-zA-Z]+$/) === -1 &&
    key.search(/^F[0-9]{1,2}$/) === -1
  );
}


const EditorTextarea = React.createClass({

  propTypes: {
    textareaComponent: React.PropTypes.func,
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

  componentWillReceiveProps(nextProps) {
    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    if (nextProps.value && nextProps.value !== null) {
      this.updateValue(nextProps.value);
    }
  },

  getMode() {
    return this.props.isRawMode ? 'raw' : 'regular';
  },

  updateValue(newValue) {
    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    this.props.onChange(newValue);

    this.setState({
      value: newValue,
    });
  },

  handleChange(e) {
    const newValue = e.target.value;
    const cleanValue = unapplyFontFilter(newValue, this.getMode());
    this.updateValue(cleanValue);
  },

  handleKeyDown(e) {
    // NOTE: The logic to handle custom overwriting selections (needed to handle
    // special cases where the newline symbol is present) is implemented using
    // the `keydown` event because the `input` event doesn't yet provide all the
    // necessary data to implement the functionality.

    if (!shouldEventOverwriteSelection(e)) {
      return;
    }

    const { selectionStart } = e.target;
    const { selectionEnd } = e.target;
    const { value } = e.target;

    // No selection: check if backspace or delete was pressed right before/after
    // a new line symbol.
    if (selectionStart === selectionEnd) {
      if (e.key === 'Backspace' && isNewlineSymbol(value[selectionStart - 1])) {
        e.preventDefault();
        this.updateValueWithSelection(value, selectionStart, selectionEnd + 1, e.key);
      } else if (e.key === 'Delete' && isNewlineSymbol(value[selectionEnd])) {
        e.preventDefault();
        this.updateValueWithSelection(value, selectionStart + 1, selectionEnd + 2, e.key);
      }
      return;
    }

    // Check whether the selection includes a newline symbol in the limits.
    // Having a selection without new line symbols will fall back to the
    // browser's default behavior.
    const start = Math.min(selectionStart, selectionEnd);
    const end = Math.max(selectionStart, selectionEnd);

    if (isNewlineSymbol(value[end - 1])) {
      e.preventDefault();
      this.updateValueWithSelection(
        value,
        (e.key !== 'Delete') ? start : start + 1,
        (e.key !== 'Delete') ? end + 1 : end + 2,
        e.key
      );
    }
  },

  updateValueWithSelection(value, start, end, keyPressed) {
    const replacementChar = (
      (keyPressed === 'Delete' || keyPressed === 'Backspace') ? '' : keyPressed
    );
    const newValue = (value.slice(0, start) + replacementChar +
                      value.slice(end, value.length));
    const cleanValue = unapplyFontFilter(newValue, this.getMode());
    this.updateValue(cleanValue);
  },

  render() {
    const transformedValue = applyFontFilter(this.state.value, this.getMode());
    const editorWrapperClasses = cx('editor-area-wrapper js-editor-area-wrapper', {
      'is-disabled': this.props.isDisabled,
    });

    return (
      <div className={editorWrapperClasses}>
        <this.props.textareaComponent
          id={this.props.id}
          initialValue={applyFontFilter(this.props.initialValue, this.getMode())}
          onChange={this.handleChange}
          onKeyDown={this.handleKeyDown}
          style={this.props.style}
          value={transformedValue}
        />
      </div>
    );
  },

});


export default EditorTextarea;
