/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import ReactDOM from 'react-dom';


const ReactRenderer = {

  nodes: [],

  render(component, node) {
    this.nodes.push(node);
    return ReactDOM.render(component, node);
  },

  unmountComponents() {
    this.nodes.forEach((node) => ReactDOM.unmountComponentAtNode(node));
    this.nodes = [];
  },

};


export default ReactRenderer;
