'use strict';

var React = require('react');

var Search = require('./search');
var LanguageForm = require('../forms').LanguageForm;
var models = require('../../models/language');


var LanguagesAdmin = React.createClass({

  render: function () {
    var viewsMap = {
      add: <LanguageAdd
              model={this.props.model}
              collection={this.props.items}
              handleSuccess={this.props.handleSave}
              handleCancel={this.props.handleCancel} />,
      edit: <LanguageEdit
              model={this.props.selectedItem}
              collection={this.props.items}
              handleAdd={this.props.handleAdd}
              handleSuccess={this.props.handleSave}
              handleDelete={this.props.handleDelete} />
    };

    var args = {
      count: this.props.items.count,
    }, msg;

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
    var resultsCaption = interpolate(msg, args, true);

    var fields = ['index', 'code', 'fullname'];

    return (
      <div className="admin-app-languages">
        <div className="module first">
          <Search
            fields={fields}
            handleSearch={this.props.handleSearch}
            handleSelectItem={this.props.handleSelectItem}
            items={this.props.items}
            selectedItem={this.props.selectedItem}
            searchLabel={gettext('Search Languages')}
            searchPlaceholder={gettext('Find language by name, code')}
            resultsCaption={resultsCaption}
            searchQuery={this.props.searchQuery} />
        </div>

        <div className="module admin-content">
          {viewsMap[this.props.view]}
        </div>
      </div>
    );
  }

});


var LanguageAdd = React.createClass({

  /* Layout */

  render: function () {
    return (
      <div className="item-add">
        <div className="hd">
          <h2>{gettext('Add Language')}</h2>
          <button
            onClick={this.props.handleCancel}
            className="btn btn-primary">{gettext('Cancel')}</button>
        </div>
        <div className="bd">
          <LanguageForm
            model={new this.props.model()}
            collection={this.props.collection}
            handleSuccess={this.props.handleSuccess} />
        </div>
      </div>
    );
  }

});


var LanguageEdit = React.createClass({

  /* Layout */

  render: function () {
    return (
      <div className="item-edit">
        <div className="hd">
          <h2>{gettext('Edit Language')}</h2>
          <button
            onClick={this.props.handleAdd}
            className="btn btn-primary">{gettext('Add Language')}</button>
        </div>
        <div className="bd">
        {!this.props.model ?
          <p>{gettext('Use the search form to find the language, then click on a language to edit.')}</p> :
          <LanguageForm
            key={this.props.model.id}
            model={this.props.model}
            collection={this.props.collection}
            handleSuccess={this.props.handleSuccess}
            handleDelete={this.props.handleDelete} />
        }
        </div>
      </div>
    );
  }

});


module.exports = {
  App: LanguagesAdmin,
  model: models.Language,
  collection: models.LanguageSet,
};
