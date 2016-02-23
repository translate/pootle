/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import React from 'react';
import AutosizeTextarea from 'react-textarea-autosize';


const Textarea = React.createClass({

  propTypes: {
    id: React.PropTypes.string,
    initialValue: React.PropTypes.string,
    onChange: React.PropTypes.func.isRequired,
    style: React.PropTypes.object,
    value: React.PropTypes.string,
  },

  contextTypes: {
    locale: React.PropTypes.string,
    localeDir: React.PropTypes.string,
  },

  componentDidUpdate() {
    /*
     * Because we need to modify the value being input by the user, we cannot
     * handle the interaction via a controlled component, because the caret
     * would always jump to the end of the text.
     * Therefore we need to use an uncontrolled component and manually handle
     * the positioning of the caret.
     */
    const node = this.refs.textarea;
    const oldLength = node.value.length;
    const oldIndex = node.selectionStart;

    node.value = this.props.value;

    const newIdx = Math.max(0, node.value.length - oldLength + oldIndex);
    node.selectionStart = node.selectionEnd = newIdx;
  },

  render() {
    const style = assign({}, {
      boxSizing: 'border-box',
      margin: '0 0 0.5em 0',
      padding: '0.3em',
    }, this.props.style);

    return (
      <AutosizeTextarea
        {...this.props}
        className="translation focusthis js-translation-area"
        defaultValue={this.props.initialValue}
        data-translation-aid={this.props.initialValue}
        dir={this.context.localeDir}
        lang={this.context.locale}
        ref="textarea"
        rows={2}
        style={style}
        tabIndex="10"
        value={undefined}
      />
    );
  },

});


export default Textarea;
