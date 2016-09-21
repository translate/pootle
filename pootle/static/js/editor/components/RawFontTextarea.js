/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import Mousetrap from 'mousetrap';
import React from 'react';
import ReactDOM from 'react-dom';

import Undoable from 'components/Undoable';
import AutosizeTextarea from 'components/AutosizeTextarea';

import {
  applyFontFilter, unapplyFontFilter, isNewlineCharacter, isNewlineSymbol,
  countNewlineCharacter, countNewlineSymbol, removeNewlineChar,
  convertNewlineSymbolToChar,
} from '../utils';


const UNDO_SHORTCUT = 'mod+z';
const REDO_SHORTCUT = 'mod+shift+z';

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


const RawFontTextarea = React.createClass({

  propTypes: {
    autoFocus: React.PropTypes.bool,
    id: React.PropTypes.string,
    initialValue: React.PropTypes.string,
    isDisabled: React.PropTypes.bool,
    isRawMode: React.PropTypes.bool,
    onChange: React.PropTypes.func.isRequired,
    onUndo: React.PropTypes.func.isRequired,
    onRedo: React.PropTypes.func.isRequired,
    style: React.PropTypes.object,
    value: React.PropTypes.string.isRequired,
  },

  contextTypes: {
    currentLocaleCode: React.PropTypes.string,
    currentLocaleDir: React.PropTypes.string,
  },

  getDefaultProps() {
    return {
      initialValue: '',
    };
  },

  componentDidMount() {
    this.mousetrap = new Mousetrap(ReactDOM.findDOMNode(this.refs.textarea));
    this.mousetrap.bind(UNDO_SHORTCUT, this.handleUndo);
    this.mousetrap.bind(REDO_SHORTCUT, this.handleRedo);

    this.isComposing = false;
    this.isDirty = false;
  },

  shouldComponentUpdate(nextProps) {
    // Avoid unnecessary re-renders when the undo stack saves snapshots but
    // Only value and mode changes should re-render the textarea — otherwise
    // there are many unnecessary re-renders when the undo stack saves snapshots.
    return (
      this.isDirty ||
      this.props.value !== nextProps.value ||
      this.props.isRawMode !== nextProps.isRawMode
    );
  },

  componentDidUpdate() {
    /*
     * Because we need to modify the value being input by the user, we cannot
     * handle the interaction via a controlled component, because the caret
     * would always jump to the end of the text.
     * Therefore we need to use an uncontrolled component and manually handle
     * the positioning of the caret.
     */

    const node = ReactDOM.findDOMNode(this.refs.textarea);
    const { selectionStart } = node;
    const { selectionEnd } = node;
    const { value } = node;

    const oldLength = node.value.length;
    const oldIndex = node.selectionStart;

    node.value = applyFontFilter(this.props.value, this.getMode());
    this.isDirty = false;

    let delta = 0;
    if (selectionStart === selectionEnd) {
      const offset = this.getSymbolOffset(value, selectionStart);
      delta = node.value.length - oldLength + offset;
    }
    node.selectionStart = node.selectionEnd = Math.max(0, delta + oldIndex);
    node.focus();
  },

  componentWillUnmount() {
    this.mousetrap.unbind(UNDO_SHORTCUT);
    this.mousetrap.unbind(REDO_SHORTCUT);
  },

  /*
   * Returns the offset to be applied on top of the normally-calculated caret
   * position.
   *
   * This is needed because:
   *  a) Removing a <LF> symbol actually removes two characters.
   *  b) Adding a character between the <LF> symbol and the NL character needs
   *     to place it one position back.
   */
  getSymbolOffset(value, selectionStart) {
    // A NL was removed
    if (isNewlineSymbol(value[selectionStart - 1]) &&
        isNewlineCharacter(value[selectionStart])) {
      return 1;
    }

    // Something was typed between the NL symbol and the NL character
    if (isNewlineSymbol(value[selectionStart - 2]) &&
        isNewlineCharacter(value[selectionStart])) {
      return -1;
    }

    return 0;
  },

  getMode() {
    return this.props.isRawMode ? 'raw' : 'regular';
  },

  _handleChange(newValue) {
    const cleanValue = unapplyFontFilter(newValue, this.getMode());
    this.isDirty = true;
    this.props.onChange(cleanValue);
  },

  handleChange(e) {
    if (this.isComposing) {
      return;
    }
    this._handleChange(e.target.value);
  },

  handleUndo(e) {
    e.preventDefault();
    this.props.onUndo();
  },

  handleRedo(e) {
    e.preventDefault();
    this.props.onRedo();
  },

  handleKeyDown(e) {
    // NOTE: The logic to handle custom overwriting selections (needed to handle
    // special cases where the newline symbol is present) is implemented using
    // the `keydown` event because the `input` event doesn't yet provide all the
    // necessary data to implement the functionality.

    if (this.isComposing || !shouldEventOverwriteSelection(e)) {
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

    this._handleChange(newValue);
  },

  handleCopyCut(e) {
    const { selectionStart } = e.target;
    const { selectionEnd } = e.target;
    const { value } = e.target;
    let selectedValue = value.slice(selectionStart, selectionEnd);

    // Special-case: the selected text contains more newline symbols than
    // actual newline characters
    if (countNewlineSymbol(selectedValue) > countNewlineCharacter(selectedValue)) {
      // 1. Remove actual newline characters
      selectedValue = removeNewlineChar(selectedValue);
      // 2. Convert symbols into actual characters
      selectedValue = convertNewlineSymbolToChar(selectedValue);
    }

    const valueToClipboard = unapplyFontFilter(selectedValue, this.getMode());
    try {
      e.clipboardData.setData('text/plain', valueToClipboard);
    } catch (exception) {
      // IE11 doesn't understand the `text/plain` content type.
      e.clipboardData.setData('Text', valueToClipboard);
    }

    e.preventDefault();
    if (e.type === 'cut') {
      const end = isNewlineSymbol(value[selectionEnd - 1])
        ? selectionEnd + 1
        : selectionEnd;
      this.updateValueWithSelection(value, selectionStart, end, 'Delete');
    }
  },

  handleComposition(e) {
    if (e.type === 'compositionend') {
      this.isComposing = false;
    } else {
      this.isComposing = true;
    }
  },

  render() {
    const style = assign({}, {
      boxSizing: 'border-box',
      margin: '0 0 0.5em 0',
      padding: '0.3em',
    }, this.props.style);

    return (
      <AutosizeTextarea
        autoFocus={this.props.autoFocus}
        className="translation focusthis js-translation-area"
        defaultValue={applyFontFilter(this.props.initialValue, this.getMode())}
        dir={this.context.currentLocaleDir}
        disabled={this.props.isDisabled}
        id={this.props.id}
        lang={this.context.currentLocaleCode}
        onChange={this.handleChange}
        onCompositionStart={this.handleComposition}
        onCompositionUpdate={this.handleComposition}
        onCompositionEnd={this.handleComposition}
        onCopy={this.handleCopyCut}
        onCut={this.handleCopyCut}
        onKeyDown={this.handleKeyDown}
        ref="textarea"
        style={style}
        value={undefined}
      />
    );
  },

});


export default new Undoable(RawFontTextarea);
