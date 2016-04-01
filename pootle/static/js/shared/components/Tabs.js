/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import { PureRenderMixin } from 'react-addons-pure-render-mixin';


const Tabs = React.createClass({

  propTypes: {
    children: React.PropTypes.node.isRequired,
    initialTab: React.PropTypes.number,
    onChange: React.PropTypes.func,
  },

  mixins: [PureRenderMixin],

  /* Lifecycle */

  getDefaultProps() {
    return {
      initialTab: 0,
    };
  },

  getInitialState() {
    return {
      selectedTab: this.props.initialTab,
    };
  },


  /* Handlers */

  handleClick(index) {
    this.setState({ selectedTab: index });

    if (this.props.onChange) {
      this.props.onChange(index);
    }
  },


  /* Layout */

  render() {
    let tabContent;

    // TODO: move to a function, retrieve values via destructuring assig.
    const tabList = React.Children.map(this.props.children, (child, index) => {
      const elementType = child.type.displayName || child.type;
      // FIXME: validate via custom propTypes
      if (elementType !== 'Tab') {
        throw new Error(`
          Invalid children for component 'Tabs'. Expected: 'Tab'.
          Found: '${elementType}'
        `);
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


export default Tabs;
