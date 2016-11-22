/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import _ from 'underscore';

import { outerHeight } from 'utils/dimensions';
import { q, qAll } from 'utils/dom';
import fetch from 'utils/fetch';

import ContentEditor from './ContentEditor';
import ContentPreview from './ContentPreview';

import './LiveEditor.css';


const SPLIT_WIDTH = 1600;
const CONTENT_MARGIN = 30;  // ~1.5em+
const WRAPPER_MARGIN = 40;  // ~2em


export const LiveEditor = React.createClass({

  propTypes: {
    markup: React.PropTypes.string.isRequired,
    // Temporarily needed to support submitting forms not controlled by JS
    name: React.PropTypes.string.isRequired,
    initialValue: React.PropTypes.string.isRequired,
  },

  getInitialState() {
    return {
      value: this.props.initialValue,
      renderedValue: '',
    };
  },

  componentWillMount() {
    if (this.props.markup === 'html') {
      this.loadPreview = () => this.setState({ renderedValue: this.state.value });
    } else {
      this.loadPreview = _.debounce(this.loadRemotePreview, 300);
    }

    this.updateDimensions();
  },

  componentDidMount() {
    this.loadPreview();

    window.addEventListener('resize', this.updateDimensions);
  },

  componentWillUnmount() {
    window.removeEventListener('resize', this.updateDimensions);
  },

  getContentHeight() {
    const topHeight = (
      outerHeight(q('#navbar')) +
      outerHeight(q('#header-meta')) +
      outerHeight(q('#header-tabs'))
    );
    const footerHeight = outerHeight(q('#footer'));

    const formFields = qAll('.js-staticpage-non-content');
    const fieldsHeight = (
      formFields.reduce((total, fieldEl) => total + outerHeight(fieldEl), 0)
    );

    const usedHeight = topHeight + fieldsHeight + footerHeight + WRAPPER_MARGIN;
    const contentHeight = this.state.height - usedHeight;

    // Actual size is divided by two in the horizontal split
    if (this.state.width <= SPLIT_WIDTH) {
      return (contentHeight - CONTENT_MARGIN) / 2;
    }

    return contentHeight;
  },

  updateDimensions() {
    // FIXME: this can perfectly be part of the single state atom, and be
    // available to any component needing it via context.
    this.setState({
      height: window.innerHeight,
      width: window.innerWidth,
    });
  },

  loadRemotePreview() {
    fetch({
      url: '/xhr/preview/',
      method: 'POST',
      body: {
        text: this.state.value,
      },
    }).then((response) => {
      this.setState({ renderedValue: response.rendered });
    });
  },

  handleChange(newValue) {
    this.setState({ value: newValue });
    this.loadPreview();
  },

  render() {
    const { renderedValue, value } = this.state;
    const minimumHeight = 300;
    const maximumHeight = 10000;
    const contentHeight = (
        Math.min(maximumHeight, Math.max(minimumHeight, this.getContentHeight()))
    );
    const contentStyle = {
      height: contentHeight,
      minHeight: minimumHeight,  // Required for Firefox
      maxHeight: maximumHeight,  // Required for Firefox
    };

    return (
      <div className="live-editor">
        <ContentEditor
          markup={this.props.markup}
          name={this.props.name}
          onChange={this.handleChange}
          style={contentStyle}
          value={value}
        />
        <ContentPreview
          style={contentStyle}
          value={renderedValue}
        />
      </div>
    );
  },

});


export default LiveEditor;
