/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import { highlightRW } from '../../utils';
import UnitPluralFormLabel from './UnitPluralFormLabel';


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


const UnitSource = React.createClass({

  propTypes: {
    id: React.PropTypes.number.isRequired,
    values: React.PropTypes.array.isRequired,
    getPluralFormName: React.PropTypes.func,
    hasPlurals: React.PropTypes.bool.isRequired,
    sourceLocaleCode: React.PropTypes.string,
    sourceLocaleDir: React.PropTypes.string,
    labelComponent: React.PropTypes.func,
    getLabel: React.PropTypes.func,
    innerComponent: React.PropTypes.func,
  },

  getDefaultProps() {
    return {
      innerComponent: InnerDiv,
      labelComponent: UnitPluralFormLabel,
    };
  },

  createItem(sourceValue, index) {
    const props = {
      lang: this.props.sourceLocaleCode,
      dir: this.props.sourceLocaleDir,
    };
    return (
      <div key={`source-value-${index}`}>
        <this.props.labelComponent
          index={index}
          hasPlurals={this.props.hasPlurals}
          getLabel={this.props.getLabel}
        />
        <div
          className="translation-text js-translation-text"
          data-string={sourceValue}
          {...props}
        >
          <this.props.innerComponent value={sourceValue} />
        </div>
      </div>
    );
  },

  render() {
    return (
      <div
        id={`js-unit-${this.props.id}`}
        className="translate-original"
      >
        {this.props.values.map(this.createItem)}
      </div>
    );
  },
});


export default UnitSource;
