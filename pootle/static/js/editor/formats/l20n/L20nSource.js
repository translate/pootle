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
import { getL20nPlurals } from './utils';


const L20nSource = React.createClass({

  propTypes: {
    values: React.PropTypes.array.isRequired,
    richModeEnabled: React.PropTypes.bool,
    sourceLocaleCode: React.PropTypes.string,
    },

  getInitialState() {
    return {
      values: this.props.values,
    };
  },

  componentWillMount() {
    const l20nPlurals = getL20nPlurals(this.props.values, 1);
    if (l20nPlurals) {
      this.setState({
        values: l20nPlurals.unitValues,
        pluralForms: l20nPlurals.pluralForms,
        hasPlurals: true,
      });
    }
  },

  componentWillReceiveProps(nextProps) {
    const l20nPlurals = getL20nPlurals(nextProps.values, 1);
    if (l20nPlurals) {
      this.setState({
        values: l20nPlurals.unitValues,
        pluralForms: l20nPlurals.pluralForms,
        hasPlurals: true,
      });
    }
  },

  getPluralFormName(index) {
    if (this.state.pluralForms !== undefined &&
        this.state.pluralForms.length === this.state.values.length) {
      return t('Plural form [%(key)s]', { key: this.state.pluralForms[index] });
    }
  },

  render() {
    return (
      <UnitSource
        {...this.props}
        {...this.state }
        getPluralFormName={this.getPluralFormName}
      />
    );
  },
});


export default L20nSource;
