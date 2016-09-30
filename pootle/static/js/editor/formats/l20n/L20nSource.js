/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import { t } from 'utils/i18n';

import UnitSource from '../../components/UnitSource';
import { getL20nData } from './utils';


const InnerPre = ({ sourceValue }) => (
  <pre
    dangerouslySetInnerHTML={
      { __html: sourceValue }
    }
  />
);

InnerPre.propTypes = {
  sourceValue: React.PropTypes.string.isRequired,
};


const L20nSource = React.createClass({

  propTypes: {
    values: React.PropTypes.array.isRequired,
    sourceLocaleCode: React.PropTypes.string,
  },

  getInitialState() {
    return {
      values: this.props.values,
      isRichModeEnabled: false,
    };
  },

  componentWillMount() {
    const l20nData = getL20nData(this.props.values);

    if (l20nData.hasL20nPlurals) {
      this.setState({
        values: l20nData.unitValues,
        pluralForms: l20nData.pluralForms,
        hasPlurals: true,
      });
    } else if (l20nData.hasSimpleValue) {
      this.setState({
        values: l20nData.unitValues,
      });
    } else {
      this.setState({
        isRichModeEnabled: true,
      });
    }
  },

  componentWillReceiveProps(nextProps) {
    if (nextProps.enableRichMode) {
      this.setState({
        values: nextProps.values,
        hasPlurals: nextProps.values.length > 1,
        isRichModeEnabled: true,
      });
    } else {
      const l20nData = getL20nData(nextProps.values);
      if (l20nData.hasL20nPlurals) {
        this.setState({
          values: l20nData.unitValues,
          pluralForms: l20nData.pluralForms,
          hasPlurals: true,
          isRichModeEnabled: false,
        });
      } else if (l20nData.hasSimpleValue) {
        this.setState({
          values: l20nData.unitValues,
          isRichModeEnabled: false,
        });
      } else {
        this.setState({
          isRichModeEnabled: true,
        });
      }
    }
  },

  getPluralFormName(index) {
    if (this.state.pluralForms !== undefined &&
        this.state.pluralForms.length === this.state.values.length) {
      return t('Plural form [%(key)s]', { key: this.state.pluralForms[index] });
    }
    return '';
  },

  render() {
    const extraProps = {};
    if (this.state.isRichModeEnabled) {
      extraProps.innerComponent = InnerPre;
    }
    return (
      <UnitSource
        {...this.props}
        {...this.state }
        {...extraProps}
        getPluralFormName={this.getPluralFormName}
      />
    );
  },
});


export default L20nSource;
