/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import { qAll } from 'utils/dom';

import Editor from '../components/Editor';
import RawFontTextarea from '../components/RawFontTextarea';
import { sym2raw } from '../utils/font';


const EditorContainer = React.createClass({

  propTypes: {
    currentLocaleCode: React.PropTypes.string.isRequired,
    currentLocaleDir: React.PropTypes.string.isRequired,

    initialValues: React.PropTypes.array,
    isDisabled: React.PropTypes.bool,
    isRawMode: React.PropTypes.bool,
    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    onChange: React.PropTypes.func.isRequired,
    overrideValues: React.PropTypes.array,
    sourceValues: React.PropTypes.array,
    style: React.PropTypes.object,
    targetNplurals: React.PropTypes.number.isRequired,
    textareaComponent: React.PropTypes.func,
    editorComponent: React.PropTypes.func,
  },

  // FIXME: move context to a higher-order component. It _cannot_ be done now
  // because we need to access the component's state in a quite hackish and
  // undesired way, and wrapping the component in a context provider would
  // prevent us from doing so.
  childContextTypes: {
    currentLocaleCode: React.PropTypes.string,
    currentLocaleDir: React.PropTypes.string,
  },

  getDefaultProps() {
    return {
      initialValues: [],
      overrideValues: null,
      textareaComponent: RawFontTextarea,
      editorComponent: Editor,
    };
  },

  getChildContext() {
    return {
      currentLocaleCode: this.props.currentLocaleCode,
      currentLocaleDir: this.props.currentLocaleDir,
    };
  },

  componentWillMount() {
    this.shouldOverride = false;
  },

  componentDidMount() {
    this.shouldOverride = false;
  },

  componentWillReceiveProps(nextProps) {
    // FIXME: this might not be needed after all :)
    if (nextProps.overrideValues) {
      // TODO: check `handleChange`/`onChange` is called as part of `setState`
      // callbacks in children
      this.props.onChange();
    }
  },

  getStateValues() {
    return qAll('.js-translation-area').map(
      (element) => sym2raw(element.value, { isRawMode: this.props.isRawMode })
    );
  },

  render() {
    // FIXME: this might not be needed after all :)
    // FIXME: this is a hack to let the underlying component with undo
    // capabilities that it should take the provided value into account to
    // keep it track in its internal history. This shouldn't be needed when
    // we remove the outside world interaction.
    const extraProps = {};
    if (this.shouldOverride) {
      extraProps.overrideValues = this.props.overrideValues;
    }

    return (
      <this.props.editorComponent
        isDisabled={this.props.isDisabled}
        isRawMode={this.props.isRawMode}
        style={this.props.style}
        targetNplurals={this.props.targetNplurals}
        textareaComponent={this.props.textareaComponent}
        initialValues={this.props.initialValues}
        onChange={this.props.onChange}
        sourceValues={this.props.sourceValues}
        {...extraProps}
      />
    );
  },

});


export default EditorContainer;
