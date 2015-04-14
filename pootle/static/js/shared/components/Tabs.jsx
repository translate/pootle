'use strict';

import cx from 'classnames';

var React = require('react');
var { PureRenderMixin } = require('react');


var Tabs = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    initialTab: React.PropTypes.number,
  },


  /* Lifecycle */

  getInitialState: function () {
    return {
      selectedTab: this.props.initialTab,
    };
  },

  getDefaultProps: function () {
    return {
      initialTab: 0,
    };
  },


  /* Handlers */

  handleClick: function (index) {
    this.setState({selectedTab: index});

    this.props.onChange && this.props.onChange(index);
  },


  /* Layout */

  render: function () {
    var elementType;
    var isActive;
    var tabContent;

    // TODO: move to a function, retrieve values via destructuring assig.
    var tabList = React.Children.map(this.props.children, function (child, index) {
      elementType = child.type.displayName || child.type;
      // FIXME: validate via custom propTypes
      if (elementType !== 'Tab') {
        throw new Error(
          'Invalid children for component `Tabs`. Expected: `Tab`. ' +
          'Found: `' + elementType + '`'
        );
      }

      isActive = this.state.selectedTab === index;
      if (isActive) {
        tabContent = child.props.children;
      }

      return React.cloneElement(child, {
          key: index,
          onClick: this.handleClick,
          selected: isActive,
          tabIndex: index,
        });
    }, this);

    return (
      <div className="Tabs">
        <ul className="Tabs__TabList">
          {tabList}
        </ul>
        <div className="Tabs__TabContent">
          {tabContent}
        </div>
      </div>
    );
  },

});


var Tab = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    onClick: React.PropTypes.func, // Required but added dynamically
    tabIndex: React.PropTypes.number, // Required but added dynamically
    title: React.PropTypes.string.isRequired,
    selected: React.PropTypes.bool,
  },


  /* Layout */

  render: function () {
    var classes = cx({
      'TabList__Tab': true,
      'TabList__Tab--is-active': this.props.selected,
    });
    var style = {
      display: 'inline-block',
      cursor: this.props.selected ? 'default' : 'pointer',
    };

    var props = {
      className: classes,
      style: style,
    };
    if (!this.props.selected) {
      props.onClick = this.props.onClick.bind(null, this.props.tabIndex);
    }

    return (
      <li {...props}>
        {this.props.title}
      </li>
    );
  },

});


module.exports = {
  Tabs: Tabs,
  Tab: Tab,
};
