/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import diff from 'utils/diff';

import UnitPluralFormLabel from './UnitPluralFormLabel';


const InnerDiv = ({ value, initialValue }) => (
  <div
    dangerouslySetInnerHTML={
      // diff() already contains highlightRO()
      { __html: diff(initialValue, value) }
    }
  />
);

InnerDiv.propTypes = {
  value: React.PropTypes.string.isRequired,
  initialValue: React.PropTypes.string.isRequired,
};


const SuggestionValue = React.createClass({

  propTypes: {
    id: React.PropTypes.number.isRequired,
    values: React.PropTypes.array.isRequired,
    hasPlurals: React.PropTypes.bool.isRequired,
    sourceLocaleCode: React.PropTypes.string,
    sourceLocaleDir: React.PropTypes.string,
    innerComponent: React.PropTypes.func,
    initialValues: React.PropTypes.array.isRequired,
    labelComponent: React.PropTypes.func,
    getLabel: React.PropTypes.func,
  },

  getDefaultProps() {
    return {
      innerComponent: InnerDiv,
      initialValues: [],
      labelComponent: UnitPluralFormLabel,
    };
  },

  createItem(value, index) {
    const initialValue = this.props.initialValues.length > index ?
      this.props.initialValues[index] : '';
    return (
      <div
        key={`source-value-${index}`}
        className="extra-item-content"
      >
        <div className="extra-item">
          <this.props.labelComponent
            index={index}
            isShort={true}
            hasPlurals={this.props.hasPlurals}
            getLabel={this.props.getLabel}
          />
          <div
            className="js-suggestion-text suggestion-translation"
            data-string={value}
            lang={this.props.sourceLocaleCode}
            dir={this.props.sourceLocaleDir}
          >
            <this.props.innerComponent
              value={value}
              initialValue={initialValue}
            />
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

