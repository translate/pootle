import cx from 'classnames';
import React from 'react';
import { PureRenderMixin } from 'react';


export const Tabs = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    initialTab: React.PropTypes.number,
  },


  /* Lifecycle */

  getInitialState() {
    return {
      selectedTab: this.props.initialTab,
    };
  },

  getDefaultProps() {
    return {
      initialTab: 0,
    };
  },


  /* Handlers */

  handleClick(index) {
    this.setState({selectedTab: index});

    this.props.onChange && this.props.onChange(index);
  },


  /* Layout */

  render() {
    let tabContent;

    // TODO: move to a function, retrieve values via destructuring assig.
    const tabList = React.Children.map(this.props.children, (child, index) => {
      const elementType = child.type.displayName || child.type;
      // FIXME: validate via custom propTypes
      if (elementType !== 'Tab') {
        throw new Error(
          'Invalid children for component `Tabs`. Expected: `Tab`. ' +
          'Found: `' + elementType + '`'
        );
      }

      const isActive = this.state.selectedTab === index;
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


export const Tab = React.createClass({
  mixins: [PureRenderMixin],

  propTypes: {
    onClick: React.PropTypes.func, // Required but added dynamically
    tabIndex: React.PropTypes.number, // Required but added dynamically
    title: React.PropTypes.string.isRequired,
    selected: React.PropTypes.bool,
  },


  /* Layout */

  render() {
    const classes = cx({
      'TabList__Tab': true,
      'TabList__Tab--is-active': this.props.selected,
    });
    const style = {
      display: 'inline-block',
      cursor: this.props.selected ? 'default' : 'pointer',
    };

    const props = {
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
