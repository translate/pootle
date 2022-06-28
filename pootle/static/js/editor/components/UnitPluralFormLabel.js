/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import { t } from 'utils/i18n';


const UnitPluralFormLabel = React.createClass({

  propTypes: {
    index: React.PropTypes.number.isRequired,
    hasPlurals: React.PropTypes.bool,
    isShort: React.PropTypes.bool,
    className: React.PropTypes.string,
  },

  getDefaultProps() {
    return {
      isShort: false,
      className: 'plural-form-label',
      hasPlurals: true,
    };
  },

  getPluralFormTitle() {
    if (this.props.isShort) {
      return `[${this.props.index}]`;
    }
    return t('Plural form %(index)s', { index: this.props.index });
  },

  render() {
    if (!this.props.hasPlurals) {
      return null;
    }

    return (
      <div className={this.props.className}>
        { this.getPluralFormTitle() }
      </div>
    );
  },

});


export default UnitPluralFormLabel;
