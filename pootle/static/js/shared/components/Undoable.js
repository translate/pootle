/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import _ from 'underscore';


const Undoable = (Component) => React.createClass({
  displayName: 'Undoable',

  propTypes: {
    initialValue: React.PropTypes.any.isRequired,
    overrideValue: React.PropTypes.any,
    onChange: React.PropTypes.func.isRequired,
  },

  getInitialState() {
    return {
      undo: [],
      value: this.props.initialValue,
      redo: [],
    };
  },

  componentWillMount() {
    this.saveSnapshot = _.debounce(this.saveSnapshot, 300);
  },

  componentWillReceiveProps(nextProps) {
    // FIXME: this is a hack to support external components adding items right
    // away to the history of changes. It should be removed in the future, once
    // `Editor` is free of outside world interactions.
    if (nextProps.overrideValue &&
        this.props.overrideValue !== nextProps.overrideValue) {
      this.saveSnapshot(nextProps.overrideValue);
    }
  },

  saveSnapshot(value) {
    if (value === this.state.value) {
      return;
    }

    this.setState({
      undo: [...this.state.undo, this.state.value],
      value,
      redo: [],
    });
  },

  handleChange(newValue) {
    this.props.onChange(newValue);
    this.saveSnapshot(newValue);
  },

  handleUndo() {
    if (this.state.undo.length === 0) {
      return;
    }

    const undo = this.state.undo.slice();
    const newValue = undo.slice(-1)[0];
    this.props.onChange(newValue);

    this.setState({
      undo: undo.slice(0, -1),
      value: newValue,
      redo: [...this.state.redo, this.state.value],
    });
  },

  handleRedo() {
    if (this.state.redo.length === 0) {
      return;
    }

    const redo = this.state.redo.slice();
    const newValue = redo.slice(-1)[0];
    this.props.onChange(newValue);

    this.setState({
      undo: [...this.state.undo, this.state.value],
      value: newValue,
      redo: this.state.redo.slice(0, -1),
    });
  },

  render() {
    return (
      <Component
        {...this.state}
        {...this.props}
        onChange={this.handleChange}
        onUndo={this.handleUndo}
        onRedo={this.handleRedo}
      />
    );
  },

});


export default Undoable;
