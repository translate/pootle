/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import { t } from 'utils/i18n';
import { qAll } from 'utils/dom';

import Editor from '../../components/Editor';
import RawFontTextarea from '../../components/RawFontTextarea';

import L20nCodeMirror from './L20nCodeMirror';

import {
  dumpL20nPlurals,
  dumpL20nValue,
  getL20nEmptyPluralsEntity,
  getL20nData,
} from './utils';


const L20nEditorContainer = React.createClass({

  propTypes: {
    currentLocaleCode: React.PropTypes.string.isRequired,
    currentLocaleDir: React.PropTypes.string.isRequired,

    initialValues: React.PropTypes.array,
    isDisabled: React.PropTypes.bool,
    isRawMode: React.PropTypes.bool,
    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    onChange: React.PropTypes.func.isRequired,
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
      textareaComponent: RawFontTextarea,
      editorComponent: Editor,
    };
  },

  getInitialState() {
    return {
      hasL20nPlurals: false,
      isRichModeEnabled: false,
      values: this.props.initialValues,
      l20nValues: this.props.initialValues,
    };
  },

  getChildContext() {
    return {
      currentLocaleCode: this.props.currentLocaleCode,
      currentLocaleDir: this.props.currentLocaleDir,
    };
  },

  componentWillMount() {
    const l20nData = getL20nData(
      this.props.initialValues,
      this.props.targetNplurals
    );
    if (l20nData.isEmpty) {
      const l20nSourceData = getL20nData(
        this.props.sourceValues,
        this.props.sourceValues.length
      );
      if (l20nSourceData.hasL20nPlurals) {
        const l20nEmptyEntity = getL20nEmptyPluralsEntity(this.props.currentLocaleCode);
        this.l20nUnitEntity = l20nEmptyEntity.unitEntity;
        this.l20nInitialValues = new Array(l20nEmptyEntity.pluralForms.length).fill('');
        this.pluralForms = l20nEmptyEntity.pluralForms;

        this.setState({
          hasL20nPlurals: true,
          l20nValues: this.l20nInitialValues,
        });
      } else if (!l20nSourceData.hasSimpleValue) {
        this.setState({
          isRichModeEnabled: true,
        });
      }
    } else if (l20nData.hasL20nPlurals) {
      this.l20nUnitEntity = l20nData.unitEntity;
      this.l20nInitialValues = l20nData.unitValues;
      this.pluralForms = l20nData.pluralForms;

      this.setState({
        hasL20nPlurals: true,
        l20nValues: this.l20nInitialValues,
      });
    } else if (l20nData.hasSimpleValue) {
      this.l20nInitialValues = l20nData.unitValues;
      this.setState({
        l20nValues: l20nData.unitValues,
      });
    } else {
      this.setState({
        isRichModeEnabled: true,
      });
    }
  },

  componentDidMount() {
    this.areas = qAll('.js-translation-area');
  },

  getAreas() {
    return this.areas;
  },

  getPluralFormName(index) {
    if (this.state.hasL20nPlurals
        && this.l20nInitialValues.length === this.pluralForms.length) {
      return t('Plural form [%(name)s]', { name: this.pluralForms[index] });
    }
    return '';
  },

  getStateValues() {
    return this.state.values;
  },

  handleChange(i, value) {
    const newValues = this.state.l20nValues.slice();
    newValues[i] = value;

    if (this.state.hasL20nPlurals && !this.state.isRichModeEnabled) {
      try {
        this.setState({
          values: dumpL20nPlurals(newValues, this.l20nUnitEntity),
          l20nValues: newValues,
        }, this.props.onChange);
      } catch (e) {
        if (e.name === 'L20nEditorError') {
          this.setState({ l20nValues: newValues });
        } else {
          throw e;
        }
      }
    } else {
      let newStateValue = value;
      if (!this.state.isRichModeEnabled) {
        newStateValue = dumpL20nValue(value);
      }
      this.setState({
        values: [newStateValue],
        l20nValues: [value],
      }, this.props.onChange);
    }
  },

  render() {
    const targetNplurals = this.state.hasL20nPlurals ? this.l20nInitialValues.length : 1;
    const textareaComponent = this.state.isRichModeEnabled ? L20nCodeMirror
                                                           : this.props.textareaComponent;
    return (
      <this.props.editorComponent
        getPluralFormName={this.getPluralFormName}
        hasL20nPlurals={this.state.hasL20nPlurals}
        initialValues={this.l20nInitialValues}
        isDisabled={this.props.isDisabled}
        isRawMode={this.props.isRawMode}
        isRichModeEnabled={this.state.isRichModeEnabled}
        onChange={this.handleChange}
        sourceValues={this.props.sourceValues}
        style={this.props.style}
        targetNplurals={targetNplurals}
        textareaComponent={textareaComponent}
        values={this.state.l20nValues}
      />
    );
  },

});


export default L20nEditorContainer;
