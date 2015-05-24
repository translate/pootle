/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

import cx from 'classnames';

var React = require('react');
var _ = require('underscore');


var Search = React.createClass({

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

  getInitialState: function () {
    return {
      isLoading: false,
    };
  },


  /* State-changing callbacks */

  fetchResults: function (query) {
    this.setState({isLoading: true});
    this.props.onSearch(query).then(this.onResultsFetched);
  },

  onResultsFetched: function (data) {
    this.setState({isLoading: false});
  },

  loadMore: function () {
    this.fetchResults(this.props.searchQuery);
  },


  /* Layout */

  render: function () {
    var isLoading = this.state.isLoading,
        items = this.props.items,
        loadMoreBtn;

    if (items.count > 0 && items.length < items.count) {
      loadMoreBtn = <button className="btn" onClick={this.loadMore}>
                    {gettext('Load More')}
                    </button>;
    }

    var resultsClassNames = cx({
      'search-results': true,
      'loading': isLoading
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
              searchQuery={this.props.searchQuery} />
          </div>
          <div className={resultsClassNames}>
          {isLoading && this.props.items.length === 0 ?
            <div>{gettext('Loading...')}</div> :
            <div>
              <ItemTable
                fields={this.props.fields}
                items={items}
                resultsCaption={this.props.resultsCaption}
                searchQuery={this.props.searchQuery}
                selectedItem={this.props.selectedItem}
                onSelectItem={this.props.onSelectItem} />
              {loadMoreBtn}
            </div>
          }
          </div>
        </div>
      </div>
    );
  }

});


var SearchBox = React.createClass({

  propTypes: {
    onSearch: React.PropTypes.func.isRequired,
    placeholder: React.PropTypes.string,
    searchQuery: React.PropTypes.string,
  },

  /* Lifecycle */

  getInitialState: function () {
    return {
      searchQuery: this.props.searchQuery
    };
  },

  componentWillReceiveProps: function (nextProps) {
    if (nextProps.searchQuery !== this.state.searchQuery) {
      this.setState({searchQuery: nextProps.searchQuery});
    }
  },

  componentWillMount: function () {
    this.handleSearchDebounced = _.debounce(function () {
      this.props.onSearch.apply(this, [this.state.searchQuery]);
    }, 300);
  },

  componentDidMount: function () {
    React.findDOMNode(this.refs.input).focus();
  },


  /* Handlers */

  handleKeyUp: function (e) {
    var key = e.nativeEvent.keyCode;
    if (key === 27) {
      React.findDOMNode(this.refs.input).blur();
    }
  },

  onChange: function () {
    this.setState({searchQuery: React.findDOMNode(this.refs.input).value});
    this.handleSearchDebounced();
  },


  /* Layout */

  render: function () {
    return <input
             type="text"
             ref="input"
             value={this.state.searchQuery}
             onKeyUp={this.handleKeyUp}
             onChange={this.onChange}
             {...this.props} />;
  }

});


var ItemTable = React.createClass({

  propTypes: {
    fields: React.PropTypes.array.isRequired,
    items: React.PropTypes.object.isRequired,
    resultsCaption: React.PropTypes.string.isRequired,
    searchQuery: React.PropTypes.string.isRequired,
    selectedItem: React.PropTypes.object,
    onSelectItem: React.PropTypes.func.isRequired,
  },

  render: function () {
    var createRow = function (item, index) {
      return (
        <ItemTableRow
          fields={this.props.fields}
          key={item.id}
          item={item}
          index={index}
          selectedItem={this.props.selectedItem}
          onSelectItem={this.props.onSelectItem} />
        );
      };

    return (
      <table>
        <caption>{this.props.resultsCaption}</caption>
        <tbody>
        {this.props.items.map(createRow.bind(this))}
        </tbody>
      </table>
    );
  }

});


var ItemTableRow = React.createClass({

  propTypes: {
    fields: React.PropTypes.array.isRequired,
    item: React.PropTypes.object.isRequired,
    index: React.PropTypes.number.isRequired,
    selectedItem: React.PropTypes.object,
    onSelectItem: React.PropTypes.func.isRequired,
  },

  render: function () {
    var item = this.props.item,
        selectedItem = this.props.selectedItem,
        index = this.props.index,
        values = item.toJSON();

    values.index = index + 1;
    var createColumn = function (field, i) {
      return <td key={i}>{values[field]}</td>;
    };

    var classNames = cx({
      'is-selected': selectedItem && item.id === selectedItem.id,
      // FIXME: this is too coupled to certain item types
      'is-disabled': item.get('disabled'),
      'row-divider': index !== 0 && index % 10 === 0,
    });

    return (
      <tr className={classNames}
          key={item.id}
          onClick={this.props.onSelectItem.bind(null, item)}>
        {this.props.fields.map(createColumn)}
      </tr>
    );
  }

});


module.exports = Search;
