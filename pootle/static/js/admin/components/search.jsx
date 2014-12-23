'use strict';

var React = require('react/addons');
var _ = require('underscore');

var cx = React.addons.classSet;


var Search = React.createClass({

  propTypes: {
    fields: React.PropTypes.array.isRequired,
    handleSearch: React.PropTypes.func.isRequired,
    handleSelectItem: React.PropTypes.func.isRequired,
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
                fields={this.props.fields}
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

  propTypes: {
    handleSearch: React.PropTypes.func,
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
    handleSelectItem: React.PropTypes.func.isRequired,
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

  propTypes: {
    fields: React.PropTypes.array.isRequired,
    item: React.PropTypes.object.isRequired,
    index: React.PropTypes.number.isRequired,
    selectedItem: React.PropTypes.object,
    handleSelectItem: React.PropTypes.func.isRequired,
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
      'selected': selectedItem && item.id === selectedItem.id,
      'is-disabled': item.get('disabled'),
      'row-divider': index !== 0 && index % 10 === 0,
    });

    return (
      <tr className={classNames}
          key={item.id}
          onClick={this.props.handleSelectItem.bind(null, item)}>
        {this.props.fields.map(createColumn)}
      </tr>
    );
  }

});


module.exports = Search;
