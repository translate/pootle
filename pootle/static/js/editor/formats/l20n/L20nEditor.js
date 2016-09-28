/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import { t } from 'utils/i18n';

import EditingArea from '../../components/EditingArea';
import RawFontTextarea from '../../components/RawFontTextarea';
import { getAreaId } from '../../utils';

import L20nCodeMirror from './L20nCodeMirror';

import {
  dumpL20nPlurals,
  dumpL20nValue,
  getL20nEmptyPluralsEntity,
  getL20nData,
} from './utils';


const L20nEditor = React.createClass({

  propTypes: {
    initialValues: React.PropTypes.array,
    isDisabled: React.PropTypes.bool,
    isRawMode: React.PropTypes.bool,
    enableRichMode: React.PropTypes.bool,
    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    onChange: React.PropTypes.func.isRequired,
    sourceValues: React.PropTypes.array.isRequired,
    style: React.PropTypes.object,
    targetNplurals: React.PropTypes.number.isRequired,
    textareaComponent: React.PropTypes.func,
  },

  contextTypes: {
    currentLocaleCode: React.PropTypes.string,
  },

  getDefaultProps() {
    return {
      initialValues: [],
      textareaComponent: RawFontTextarea,
    };
  },

  getInitialState() {
    return {
      values: this.props.initialValues,
      targetNplurals: this.props.targetNplurals,
      hasL20nPlurals: false,
      isRichModeEnabled: false,
      pluralInitialValues: [],
      pluralForms: [],
      textareaComponent: this.props.textareaComponent,
    };
  },

  componentWillMount() {
    this.shouldUpdateValuesInChildren = false;
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
        this.hasL20nPlurals = true;
        const l20nEmptyEntity = getL20nEmptyPluralsEntity(this.context.currentLocaleCode);
        this.l20nUnitEntity = l20nEmptyEntity.unitEntity;
        const initialValues = new Array(l20nEmptyEntity.pluralForms.length).fill('');
        this.setState({
          pluralInitialValues: initialValues,
          values: initialValues,
          pluralForms: l20nEmptyEntity.pluralForms,
          targetNplurals: l20nEmptyEntity.pluralForms.length,
          hasL20nPlurals: true,
        });
      } else if (!l20nSourceData.hasSimpleValue) {
        this.setState({
          isRichModeEnabled: true,
          textareaComponent: L20nCodeMirror,
        });
      }
    } else if (l20nData.hasL20nPlurals) {
      this.l20nUnitEntity = l20nData.unitEntity;
      this.setState({
        pluralInitialValues: l20nData.unitValues,
        values: l20nData.unitValues,
        targetNplurals: l20nData.unitValues.length,
        pluralForms: l20nData.pluralForms,
        hasL20nPlurals: true,
      });
    } else if (!l20nData.hasSimpleValue) {
      this.setState({
        isRichModeEnabled: true,
        textareaComponent: L20nCodeMirror,
      });
    }
  },

  componentWillReceiveProps(nextProps) {
    if (nextProps.enableRichMode) {
      if (!this.state.isRichModeEnabled) {
        this.setState({
          values: nextProps.values,
          targetNplurals: 1,
          hasPlurals: nextProps.values.length > 1,
          isRichModeEnabled: true,
          textareaComponent: L20nCodeMirror,
        });
      }
    } else {
      const l20nData = getL20nData(nextProps.values, nextProps.targetNplurals);
      if (l20nData.isEmpty) {
        if (this.codemirror !== undefined) {
          this.codemirror.toTextArea();
          this.codemirror = undefined;
        }
        this.setState({
          isRichModeEnabled: false,
          textareaComponent: this.props.textareaComponent,
        });
      } else if (l20nData.hasL20nPlurals) {
        if (this.codemirror !== undefined) {
          this.codemirror.toTextArea();
          this.codemirror = undefined;
        }
        this.hasL20nPlurals = true;
        this.l20nUnitEntity = l20nData.unitEntity;
        this.shouldUpdateValuesInChildren = true;
        this.setState({
          values: l20nData.unitValues,
          pluralInitialValues: l20nData.unitValues,
          targetNplurals: l20nData.unitValues.length,
          pluralForms: l20nData.pluralForms,
          hasL20nPlurals: true,
          isRichModeEnabled: false,
          textareaComponent: this.props.textareaComponent,
        }, () => {
          this.shouldUpdateValuesInChildren = false;
        });
      } else if (l20nData.hasSimpleValue) {
        this.setState({
          isRichModeEnabled: false,
          hasL20nPlurals: false,
          textareaComponent: this.props.textareaComponent,
        });
      } else {
        // rich mode can't be switched off
        this.setState({
          hasL20nPlurals: false,
          isRichModeEnabled: false,
          textareaComponent: L20nCodeMirror,
        });
      }
    }
  },

  getPluralFormName(index) {
    if (this.state.pluralForms.length === this.state.values.length) {
      return t('Plural form [%(name)s]', { name: this.state.pluralForms[index] });
    }
    return '';
  },

  handleChange(i, value) {
    const newValues = this.state.values.slice();
    newValues[i] = value;

    if (this.state.hasL20nPlurals && !this.state.isRichModeEnabled) {
      try {
        const newL20nValues = dumpL20nPlurals(newValues, this.l20nUnitEntity);
        this.setState({ values: newValues }, () => this.props.onChange(0, newL20nValues[0]));
      } catch (e) {
        if (e.name === 'L20nEditorError') {
          this.setState({ values: newValues });
        } else {
          throw e;
        }
      }
    } else {
      let value = newValues[i];
      if (!this.state.isRichModeEnabled) {
        value = dumpL20nValue(value);
      }
      this.setState({ values: newValues }, () => this.props.onChange(i, value));
    }
  },

  handleCMCreate(cm) {
    this.codemirror = cm;
  },

  render() {
    const editingAreas = [];
    const initialValues = this.state.hasL20nPlurals ? this.state.pluralInitialValues
                                                    : this.props.initialValues;
    for (let i = 0; i < this.state.targetNplurals; i++) {
      const extraProps = {};
      if (this.props.isRawMode !== undefined) {
        extraProps.isRawMode = this.props.isRawMode;
      }
      // FIXME: this is a hack to let the underlying component with undo
      // capabilities that it should take the provided value into account to
      // keep it track in its internal history. This shouldn't be needed when
      // we remove the outside world interaction.
      if (this.props.overrideValues) {
        extraProps.overrideValue = this.props.overrideValues[i];
      }
      editingAreas.push(
        <EditingArea
          isDisabled={this.props.isDisabled}
          key={i}
        >
          {this.state.hasL20nPlurals && !this.state.isRichModeEnabled &&
            <div className="subheader">
              { this.getPluralFormName(i) }
            </div>
          }
          <this.state.textareaComponent
            autoFocus={i === 0}
            id={getAreaId(i)}
            initialValue={initialValues[i]}
            isDisabled={this.props.isDisabled}
            onChange={(value) => this.handleChange(i, value)}
            value={this.state.values[i]}
            {...extraProps}
            onCMCreate={this.handleCMCreate}
            shouldUpdateValue={this.shouldUpdateValuesInChildren}
          />
        </EditingArea>
      );
    }
    return (
      <div>
        {editingAreas}
      </div>
    );
  },

});


export default L20nEditor;
