/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import { t } from 'utils/i18n';

import { highlightRW } from '../../utils';


const InnerDiv = ({ value }) => (
  <div
    dangerouslySetInnerHTML={
      { __html: highlightRW(value) }
    }
  />
);

InnerDiv.propTypes = {
  value: React.PropTypes.string.isRequired,
};


const SuggestionValue = React.createClass({

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

  createItem(value, index) {
    const props = {
      lang: this.props.sourceLocaleCode,
      dir: this.props.sourceLocaleDir,
    };
    return (
      <div
        key={`source-value-${index}`}
        className="extra-item-content"
      >
        <div className="extra-item">
          {this.props.hasPlurals &&
           <div
             className="plural-form-label"
           >{ this.getPluralFormName(index) }</div>
          }
          <div
            className="js-suggestion-text suggestion-translation"
            data-string={value}
            lang={this.props.sourceLocaleCode}
          >
            <this.props.innerComponent value={value} />
          </div>
        </div>
      </div>
    );
  },

  render() {
    return (
      <div>
        {this.props.values.map(this.createItem)}
      </div>
    );
  },
});


export default SuggestionValue;

