/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React from 'react';

import { t } from 'utils/i18n';

import { highlightRW } from '../../utils';


const InnerDiv = ({ sourceValue }) => (
  <div
    dangerouslySetInnerHTML={
      { __html: highlightRW(sourceValue) }
    }
  />
);

InnerDiv.propTypes = {
  sourceValue: React.PropTypes.string.isRequired,
};


const UnitSource = React.createClass({

  propTypes: {
    id: React.PropTypes.number.isRequired,
    values: React.PropTypes.array.isRequired,
    getPluralFormName: React.PropTypes.func,
    hasPlurals: React.PropTypes.bool.isRequired,
    sourceLocaleCode: React.PropTypes.string,
    sourceLocaleDir: React.PropTypes.string,
    innerComponent: React.PropTypes.func,
  },

  getDefaultProps() {
    return {
      innerComponent: InnerDiv,
    };
  },

  getPluralFormName(index) {
    if (this.props.getPluralFormName !== undefined) {
      return this.props.getPluralFormName(index);
    }

    return t('Plural form %(index)s', { index });
  },

  createItem(sourceValue, index) {
    const props = {
      lang: this.props.sourceLocaleCode,
      dir: this.props.sourceLocaleDir,
    };
    return (
      <div key={`source-value-${index}`}>
        {this.props.hasPlurals &&
         <div
           className="plural-form-label"
         >{ this.getPluralFormName(index) }</div>
        }
        <div
          className="translation-text js-translation-text"
          data-string={sourceValue}
          {...props}
        >
          <this.props.innerComponent sourceValue={sourceValue} />
        </div>
      </div>
    );
  },

  render() {
    const classNames = cx('translate-original', {
      'translate-plural': this.props.hasPlurals,
    });

    return (
      <div
        id={`js-unit-${this.props.id}`}
        className={classNames}
      >
        {this.props.values.map(this.createItem)}
      </div>
    );
  },
});


export default UnitSource;
