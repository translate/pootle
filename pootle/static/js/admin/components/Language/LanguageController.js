/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import Search from '../Search';

import LanguageAdd from './LanguageAdd';
import LanguageEdit from './LanguageEdit';


const LanguageController = React.createClass({

  propTypes: {
    items: React.PropTypes.object.isRequired,
    model: React.PropTypes.func.isRequired,
    onAdd: React.PropTypes.func.isRequired,
    onCancel: React.PropTypes.func.isRequired,
    onDelete: React.PropTypes.func.isRequired,
    onSearch: React.PropTypes.func.isRequired,
    onSelectItem: React.PropTypes.func.isRequired,
    onSuccess: React.PropTypes.func.isRequired,
    searchQuery: React.PropTypes.string.isRequired,
    selectedItem: React.PropTypes.object,
    view: React.PropTypes.string.isRequired,
  },

  render() {
    const viewsMap = {
      add: (
        <LanguageAdd
          model={this.props.model}
          collection={this.props.items}
          onSuccess={this.props.onSuccess}
          onCancel={this.props.onCancel}
        />
      ),
      edit: (
        <LanguageEdit
          model={this.props.selectedItem}
          collection={this.props.items}
          onAdd={this.props.onAdd}
          onSuccess={this.props.onSuccess}
          onDelete={this.props.onDelete}
        />
      ),
    };
    const args = {
      count: this.props.items.count,
    };

    let msg;
    if (this.props.searchQuery) {
      msg = ngettext('%(count)s language matches your query.',
                     '%(count)s languages match your query.', args.count);
    } else {
      msg = ngettext(
        'There is %(count)s language.',
        'There are %(count)s languages. Below are the most recently added ones.',
        args.count
      );
    }
    const resultsCaption = interpolate(msg, args, true);

    return (
      <div className="admin-app-languages">
        <div className="module first">
          <Search
            fields={['index', 'code', 'fullname']}
            onSearch={this.props.onSearch}
            onSelectItem={this.props.onSelectItem}
            items={this.props.items}
            selectedItem={this.props.selectedItem}
            searchLabel={gettext('Search Languages')}
            searchPlaceholder={gettext('Find language by name, code')}
            resultsCaption={resultsCaption}
            searchQuery={this.props.searchQuery}
          />
        </div>

        <div className="module admin-content">
          {viewsMap[this.props.view]}
        </div>
      </div>
    );
  },

});


export default LanguageController;
