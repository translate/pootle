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

import {
  dumpL20nPlurals,
  getL20nEmptyPluralsEntity,
  getL20nPlurals
} from './utils';


const L20nEditor = React.createClass({

  propTypes: {
    initialValues: React.PropTypes.array,
    isDisabled: React.PropTypes.bool,
    isRawMode: React.PropTypes.bool,
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

  getInitialState() {
    return {
      values: this.props.initialValues,
      targetNplurals: this.props.targetNplurals,
      hasL20nPlurals: false,
      pluralInitialValues: [],
      pluralForms: [],
    };
  },

  getDefaultProps() {
    return {
      initialValues: [],
      textareaComponent: RawFontTextarea,
    };
  },

  componentWillMount() {
    const l20nPlurals = getL20nPlurals(
      this.props.initialValues,
      this.props.targetNplurals
    );
    if (l20nPlurals) {
      this.l20nUnitEntity = l20nPlurals.unitEntity;
      this.setState({
        pluralInitialValues: l20nPlurals.unitValues,
        values: l20nPlurals.unitValues,
        targetNplurals: l20nPlurals.unitValues.length,
        pluralForms: l20nPlurals.pluralForms,
        hasL20nPlurals: true,
      });
    } else {
      const l20nSourcePlurals = getL20nPlurals(
        this.props.sourceValues,
        this.props.sourceValues.length
      );
      if (l20nSourcePlurals) {
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
      }
    }
  },

  componentWillReceiveProps(nextProps) {
    const l20nPlurals = getL20nPlurals(this.state.values, nextProps.targetNplurals);
    if (l20nPlurals) {
      this.hasL20nPlurals = true;
      this.l20nUnitEntity = l20nPlurals.unitEntity;
      this.setState({
        values: l20nPlurals.unitValues,
        targetNplurals: l20nPlurals.unitValues.length,
        hasL20nPlurals: true,
      });
    }
  },

  handleChange(i, value) {
    const newValues = this.state.values.slice();
    newValues[i] = value;

    if (this.state.hasL20nPlurals) {
      try {
        const newL20nValues = dumpL20nPlurals(newValues, this.l20nUnitEntity);
        this.setState({ values: newValues }, () => this.props.onChange(0, newL20nValues[0]));
      } catch (e) {
        if (e instanceof Error) {
          this.setState({ values: newValues });
        } else {
          throw e;
        }
      }
    } else {
      this.setState({ values: newValues }, () => this.props.onChange(i, newValues[i]));
    }
  },

  getPluralFormName(index) {
    if (this.state.pluralForms.length === this.state.values.length) {
      return t('Plural form [%(name)s]', { name: this.state.pluralForms[index] });
    }
    return t('Plural form %(index)s', { index });
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

      editingAreas.push(
        <EditingArea
          isDisabled={this.props.isDisabled}
          key={i}
        >
          {this.state.hasL20nPlurals &&
            <div className="subheader">
              { this.getPluralFormName(i) }
            </div>
          }
          <this.props.textareaComponent
            autoFocus={i === 0}
            id={getAreaId(i)}
            initialValue={initialValues[i]}
            isDisabled={this.props.isDisabled}
            onChange={(value) => this.handleChange(i, value)}
            value={this.state.values[i]}
            {...extraProps}
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


