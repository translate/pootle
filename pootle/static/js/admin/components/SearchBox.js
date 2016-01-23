/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import _ from 'underscore';


const SearchBox = React.createClass({

  propTypes: {
    onSearch: React.PropTypes.func.isRequired,
    placeholder: React.PropTypes.string,
    searchQuery: React.PropTypes.string,
  },

  /* Lifecycle */

  getInitialState() {
    return {
      // XXX: review, prop should be explicitly named `initialSearchQuery`
      searchQuery: this.props.searchQuery,
    };
  },

  componentWillMount() {
    this.handleSearchDebounced = _.debounce(() => {
      this.props.onSearch.apply(this, [this.state.searchQuery]);
    }, 300);
  },

  componentDidMount() {
    this.refs.input.focus();
  },

  componentWillReceiveProps(nextProps) {
    if (nextProps.searchQuery !== this.state.searchQuery) {
      this.setState({ searchQuery: nextProps.searchQuery });
    }
  },


  /* Handlers */

  handleKeyUp(e) {
    const key = e.nativeEvent.keyCode;
    if (key === 27) {
      this.refs.input.blur();
    }
  },

  handleChange() {
    this.setState({ searchQuery: this.refs.input.value });
    this.handleSearchDebounced();
  },


  /* Layout */

  render() {
    return (
      <input
        type="text"
        ref="input"
        value={this.state.searchQuery}
        onChange={this.handleChange}
        onKeyUp={this.handleKeyUp}
        {...this.props}
      />
    );
  },

});


export default SearchBox;
