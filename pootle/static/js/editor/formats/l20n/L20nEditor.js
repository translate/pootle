/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import Editor from '../../containers/Editor';
import {
  dumpL20nPlurals,
  getL20nEmptyPluralsEntity,
  getL20nPlurals
} from './utils';


const L20nEditor = React.createClass({

  propTypes: {
    initialValues: React.PropTypes.array,
    isRichModeEnabled: React.PropTypes.bool,
    targetNplurals: React.PropTypes.number.isRequired,
    onChange: React.PropTypes.func.isRequired,
  },

  params: {},

  getInitialState() {
    return {
      initialValues: this.props.initialValues,
      targetNplurals: this.props.targetNplurals,
      values: this.props.initialValues,
    };
  },

  onChange(values) {
    if (!this.hasL20nPlurals) {
      return values;
    }
    this.setState(
      {values: dumpL20nPlurals(values, this.l20nUnitEntity)},
      this.props.onChange
    );
  },

  componentWillMount() {
    this.params.initialValues = this.props.initialValues;
    this.params.targetNplurals = this.props.targetNplurals;

    if (this.props.isRichModeEnabled) {
      return false;
    }

    const l20nPlurals = getL20nPlurals(
      this.props.initialValues,
      this.props.targetNplurals
    );
    if (l20nPlurals) {
      this.hasL20nPlurals = true;
      this.l20nUnitEntity = l20nPlurals.unitEntity;
      this.params.initialValues = l20nPlurals.unitValues;
      this.pluralInitialValues = this.params.initialValues;
      this.params.targetNplurals = l20nPlurals.unitValues.length;
    } else {
      const l20nSourcePlurals = getL20nPlurals(
        this.props.sourceValues,
        this.props.sourceValues.length
      );
      if (l20nSourcePlurals) {
        this.hasL20nPlurals = true;
        const l20nEmptyEntity = getL20nEmptyPluralsEntity(this.props.currentLocaleCode);
        this.l20nUnitEntity = l20nEmptyEntity.unitEntity;
        this.params.initialValues  = new Array(l20nEmptyEntity.length).fill('');
        this.pluralInitialValues = this.params.initialValues;
        this.params.targetNplurals = this.params.initialValues.length;
      }
    }
  },

  componentWillReceiveProps(nextProps) {
    this.params.initialValues = nextProps.initialValues;
    this.params.targetNplurals = nextProps.targetNplurals;
    this.params.overrideValues = this.state.values;
    this.params.shouldTriggerChange = false;

    if (nextProps.isRichModeEnabled) {
      return false;
    }

    const l20nPlurals = getL20nPlurals(this.state.values, nextProps.targetNplurals);
    if (l20nPlurals) {
      this.hasL20nPlurals = true;
      this.l20nUnitEntity = l20nPlurals.unitEntity;
      this.params.initialValues = this.pluralInitialValues;
      this.params.overrideValues = l20nPlurals.unitValues;
      this.params.targetNplurals = l20nPlurals.unitValues.length;
    }
  },

  render() {
    return (
      <Editor
        {...this.props}
        {...this.params}
        onChange={this.onChange}
      />
    );
  }

});


export default L20nEditor;


