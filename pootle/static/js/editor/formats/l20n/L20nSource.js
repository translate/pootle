/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import UnitSource from '../../components/UnitSource';
import { getL20nPlurals } from './utils';

import { t } from 'utils/i18n';


const L20nSource = React.createClass({

  propTypes: {
    values: React.PropTypes.array.isRequired,
    richModeEnabled: React.PropTypes.bool,
  },

  getInitialState() {
    return {
      values: this.props.values,
    };
  },

  componentDidMount() {
    const l20nPlurals = getL20nPlurals(this.props.values, 1);
    if (l20nPlurals) {
      this.setState({
        values: l20nPlurals.unitValues,
        hasPlurals: true,
      });
    }
  },

  componentWillReceiveProps(nextProps) {
    if (nextProps.isRichModeEnabled) {
      this.setState({
        values: nextProps.values,
        hasPlurals: nextProps.values.length > 1,
      });
    } else {
      const l20nPlurals = getL20nPlurals(nextProps.values, 1);
      if (l20nPlurals) {
        this.setState({
          values: l20nPlurals.unitValues,
          hasPlurals: true,
        });
      }
    }
  },

  render() {
    return (
      <UnitSource {...this.props} {...this.state } />
    );
  },
});


export default L20nSource;
