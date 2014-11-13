'use strict';

var React = require('react/addons');
var _ = require('underscore');

var cx = React.addons.classSet;


var Search = React.createClass({

  /* Lifecycle */

  getInitialState: function () {
    return {
      isLoading: false,
    };
  },


  /* State-changing callbacks */

  fetchResults: function (query) {
    this.setState({isLoading: true});
    this.props.handleSearch(query).then(this.onResultsFetched);
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
              handleSearch={this.props.handleSearch}
              placeholder={this.props.searchPlaceholder}
              searchQuery={this.props.searchQuery} />
          </div>
          <div className={resultsClassNames}>
          {isLoading && this.props.items.length === 0 ?
            <div>{gettext('Loading...')}</div> :
            <div>
              <ItemTable
                items={items}
                resultsCaption={this.props.resultsCaption}
                searchQuery={this.props.searchQuery}
                selectedItem={this.props.selectedItem}
                handleSelectItem={this.props.handleSelectItem} />
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

  componentDidMount: function () {
    this.refs.input.getDOMNode().focus();
  },


  /* Handlers */

  handleKeyUp: function (e) {
    var key = e.nativeEvent.keyCode;
    if (key === 27) {
      this.refs.input.getDOMNode().blur();
    }
  },

  handleSearchDebounced: _.debounce(function () {
    this.props.handleSearch.apply(this, [this.state.searchQuery]);
  }, 300),

  onChange: function () {
    this.setState({searchQuery: this.refs.input.getDOMNode().value});
    this.handleSearchDebounced();
  },


  /* Layout */

  render: function () {
    return this.transferPropsTo(
      <input
        type="text"
        ref="input"
        value={this.state.searchQuery}
        onKeyUp={this.handleKeyUp}
        onChange={this.onChange} />
    );
  }

});


var ItemTable = React.createClass({

  render: function () {
    var createRow = function (item, index) {
      return (
        <ItemTableRow
          key={item.id}
          item={item}
          index={index}
          selectedItem={this.props.selectedItem}
          handleSelectItem={this.props.handleSelectItem} />
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

  render: function () {
    var item = this.props.item,
        selectedItem = this.props.selectedItem,
        values = item.toJSON();

    values.index = item.displayIndex();
    // FIXME: pass fields as `props`
    var fields = ['index', 'full_name', 'username', 'email'];
    var createColumn = function (field, i) {
      return <td key={i}>{values[field]}</td>;
    };

    var classNames = cx({
      'selected': selectedItem && item.id === selectedItem.id,
      'row-divider': (values.index - 1) !== 0 && (values.index - 1) % 10 === 0
    });

    return (
      <tr className={classNames}
          key={item.id}
          onClick={this.props.handleSelectItem.bind(null, item)}>
        {fields.map(createColumn)}
      </tr>
    );
  }

});


module.exports = Search;
