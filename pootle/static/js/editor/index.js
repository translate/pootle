/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import React from 'react';

import ReactRenderer from 'utils/ReactRenderer';

import Editor from './containers/Editor';


const ReactEditor = {

  init(props) {
    this.node = document.querySelector('.js-mount-editor');
    this.props = {};

    ReactRenderer.unmountComponents();

    this.setProps(props);
  },

  setProps(props) {
    // Overriding values is a one-time thing: take it into account only if it
    // was passed explicitly.
    const overrideProps = (
      props.hasOwnProperty('overrideValues') ? {} : { overrideValues: null }
    );
    this.props = assign(this.props, props, overrideProps);

    this.editorInstance = ReactRenderer.render(
      <Editor
        onChange={this.handleChange}
        {...this.props}
      />,
      this.node
    );
  },

  // FIXME: this additional layer of state tracking is only kept to allow
  // interaction from the outside world. Remove ASAP.
  get stateValues() {
    return this.editorInstance.state.values;
  },

  handleChange() {
    PTL.editor.onTextareaChange();
  },

};


export default ReactEditor;
