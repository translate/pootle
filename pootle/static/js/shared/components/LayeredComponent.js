/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 *
 * Original idea: https://github.com/Khan/react-components
 */

import React from 'react';
import ReactDOM from 'react-dom';


const LayeredComponent = React.createClass({

  propTypes: {
    children: React.PropTypes.node.isRequired,
  },

  componentDidMount() {
    this.layer = document.createElement('div');
    document.body.appendChild(this.layer);
    this.renderLayer();
  },

  componentDidUpdate() {
    this.renderLayer();
  },

  componentWillUnmount() {
    ReactDOM.unmountComponentAtNode(this.layer);
    document.body.removeChild(this.layer);
  },

  renderLayer() {
    ReactDOM.render(this.props.children, this.layer);
  },

  render() {
    return null;
  },

});


export default LayeredComponent;
