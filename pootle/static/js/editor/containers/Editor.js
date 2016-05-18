/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import EditingArea from '../components/EditingArea';
import RawFontTextarea from '../components/RawFontTextarea';
import { getAreaId } from '../utils';


const Editor = React.createClass({

  propTypes: {
    initialValues: React.PropTypes.array,
    isDisabled: React.PropTypes.bool,
    isRawMode: React.PropTypes.bool,
    locale: React.PropTypes.string,
    localeDir: React.PropTypes.string,
    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    onChange: React.PropTypes.func.isRequired,
    overrideValues: React.PropTypes.array,
    sourceString: React.PropTypes.string.isRequired,
    style: React.PropTypes.object,
    targetNplurals: React.PropTypes.number.isRequired,
    textareaComponent: React.PropTypes.func,
  },

  // FIXME: move context to a higher-order component. It _cannot_ be done now
  // because we need to access the component's state in a quite hackish and
  // undesired way, and wrapping the component in a context provider would
  // prevent us from doing so.
  childContextTypes: {
    locale: React.PropTypes.string,
    localeDir: React.PropTypes.string,
  },

  getDefaultProps() {
    return {
      initialValues: [],
      overrideValues: null,
      textareaComponent: RawFontTextarea,
    };
  },

  getInitialState() {
    return {
      values: this.props.initialValues,
    };
  },

  getChildContext() {
    return {
      locale: this.props.locale,
      localeDir: this.props.localeDir,
    };
  },

  componentWillReceiveProps(nextProps) {
    if (nextProps.overrideValues) {
      // FIXME: Using the second argument callback to `setState` to ensure the
      // callback is run after re-rendering happened, so that the DOM-based
      // editor can perform any operations safely. This is needed to allow
      // interaction from the outside world. Remove ASAP.
      this.setState({
        values: nextProps.overrideValues,
      }, this.props.onChange);
    }
  },

  handleChange(i, value) {
    const newValues = this.state.values.slice();
    newValues[i] = value;

    // FIXME: Using the second argument callback to `setState` to ensure the
    // callback is run after re-rendering happened, so that the DOM-based
    // editor can perform any operations safely. This is needed to allow
    // interaction from the outside world. Remove ASAP.
    this.setState({
      values: newValues,
    }, this.props.onChange);
  },

  render() {
    const editingAreas = [];

    for (let i = 0; i < this.props.targetNplurals; i++) {
      const extraProps = {
        isDisabled: this.props.isDisabled,
        textareaComponent: this.props.textareaComponent,
      };
      if (this.props.isRawMode !== undefined) {
        extraProps.isRawMode = this.props.isRawMode;
      }
      editingAreas.push(
        <EditingArea
          id={getAreaId(i)}
          initialValue={this.props.initialValues[i]}
          key={i}
          onChange={(value) => this.handleChange(i, value)}
          value={this.state.values[i]}
          {...extraProps}
        />
      );
    }
    return (
      <div>
        {editingAreas}
      </div>
    );
  },

});


export default Editor;
