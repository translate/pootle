/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React from 'react';

import ItemTable from './ItemTable';
import SearchBox from './SearchBox';


const Search = React.createClass({

  propTypes: {
    fields: React.PropTypes.array.isRequired,
    onSearch: React.PropTypes.func.isRequired,
    onSelectItem: React.PropTypes.func.isRequired,
    items: React.PropTypes.object.isRequired,
    selectedItem: React.PropTypes.object,
    searchLabel: React.PropTypes.string.isRequired,
    searchPlaceholder: React.PropTypes.string.isRequired,
    resultsCaption: React.PropTypes.string.isRequired,
    searchQuery: React.PropTypes.string.isRequired,
  },

  /* Lifecycle */

  getInitialState() {
    return {
      isLoading: false,
    };
  },


  /* State-changing callbacks */

  onResultsFetched() {
    this.setState({ isLoading: false });
  },

  fetchResults(query) {
    this.setState({ isLoading: true });
    this.props.onSearch(query).then(this.onResultsFetched);
  },

  loadMore() {
    this.fetchResults(this.props.searchQuery);
  },


  /* Layout */

  render() {
    const { isLoading } = this.state;
    const { items } = this.props;
    let loadMoreBtn;

    if (items.count > 0 && items.length < items.count) {
      loadMoreBtn = (
        <button
          className="btn"
          onClick={this.loadMore}
        >
          {gettext('Load More')}
        </button>
      );
    }

    const resultsClassNames = cx({
      'search-results': true,
      loading: isLoading,
    });

    return (
      <div className="search">
        <div className="hd">
          <h2>{this.props.searchLabel}</h2>
        </div>
        <div className="bd">
          <div className="search-box">
            <SearchBox
              onSearch={this.props.onSearch}
              placeholder={this.props.searchPlaceholder}
              searchQuery={this.props.searchQuery}
            />
          </div>
          <div className={resultsClassNames}>
          {isLoading && this.props.items.length === 0 ?
            <div>{gettext('Loading...')}</div> :
            <div>
              <ItemTable
                fields={this.props.fields}
                items={items}
                resultsCaption={this.props.resultsCaption}
                selectedItem={this.props.selectedItem}
                onSelectItem={this.props.onSelectItem}
              />
              {loadMoreBtn}
            </div>
          }
          </div>
        </div>
      </div>
    );
  },

});


export default Search;
