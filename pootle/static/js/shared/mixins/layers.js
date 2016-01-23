// Source: https://github.com/Khan/react-components
// MIT License
// Copyright (c) 2014 Khan Academy

// From http://jsfiddle.net/LBAr8/

/* Create a new "layer" on the page, like a modal or overlay.
 *
 * const LayeredComponent = React.createClass({
 *     mixins: [LayeredComponentMixin],
 *     render() {
 *         // render like usual
 *     },
 *     renderLayer() {
 *         // render a separate layer (the modal or overlay)
 *     }
 * });
 */

import React from 'react';
import ReactDOM from 'react-dom';


const LayeredComponentMixin = {

  componentDidMount() {
        // Appending to the body is easier than managing the z-index of
        // everything on the page.  It's also better for accessibility and
        // makes stacking a snap (since components will stack in mount order).
    this._layer = document.createElement('div');
    document.body.appendChild(this._layer);
    this._renderLayer();
  },

  componentDidUpdate() {
    this._renderLayer();
  },

  componentWillUnmount() {
    this._unrenderLayer();
    document.body.removeChild(this._layer);
  },

  _renderLayer() {
        // By calling this method in componentDidMount() and
        // componentDidUpdate(), you're effectively creating a "wormhole" that
        // funnels React's hierarchical updates through to a DOM node on an
        // entirely different part of the page.

    const layerElement = this.renderLayer();
        // Renders can return null, but React.render() doesn't like being asked
        // to render null. If we get null back from renderLayer(), just render
        // a noscript element, like React does when an element's render returns
        // null.
    if (layerElement === null) {
      ReactDOM.render(React.DOM.noscript, this._layer);
    } else {
      ReactDOM.render(layerElement, this._layer);
    }

    if (this.layerDidMount) {
      this.layerDidMount(this._layer);
    }
  },

  _unrenderLayer() {
    if (this.layerWillUnmount) {
      this.layerWillUnmount(this._layer);
    }

    ReactDOM.unmountComponentAtNode(this._layer);
  },

};


export default LayeredComponentMixin;
