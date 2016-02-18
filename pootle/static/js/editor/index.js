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

    // FIXME: this additional layer of state tracking is only kept to allow
    // interaction from the outside world. Remove ASAP.
    this.state = {
      values: props.initialValues.slice(),
    };

    ReactRenderer.unmountComponents();

    this.setProps(props);
  },

  setProps(props) {
    this.props = assign(this.props, props);

    ReactRenderer.render(
      <Editor
        onChange={(name, value) => this.handleValueChange(name, value)}
        {...this.props}
      />,
      this.node
    );
  },

  handleValueChange(index, value) {
    // FIXME: this additional layer of state tracking is only kept to allow
    // interaction from the outside world. Remove ASAP.
    this.state.values[index] = value;
  },

};


export default ReactEditor;
