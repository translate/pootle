'use strict';

var React = require('react');

var Search = require('./search');
var ProjectForm = require('forms').ProjectForm;
var models = require('models/project');


var ProjectsAdmin = React.createClass({

  render: function () {
    var viewsMap = {
      add: <ProjectAdd
              model={this.props.model}
              collection={this.props.items}
              handleSuccess={this.props.handleSave}
              handleCancel={this.props.handleCancel} />,
      edit: <ProjectEdit
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
      msg = ngettext('%(count)s project matches your query.',
                     '%(count)s projects match your query.', args.count);
    } else {
      msg = ngettext(
        'There is %(count)s project.',
        'There are %(count)s projects. Below are the most recently added ones.',
        args.count
      );
    }
    var resultsCaption = interpolate(msg, args, true);

    var fields = ['index', 'code', 'fullname', 'disabled'];

    return (
      <div className="admin-app-projects">
        <div className="module first">
          <Search
            fields={fields}
            handleSearch={this.props.handleSearch}
            handleSelectItem={this.props.handleSelectItem}
            items={this.props.items}
            selectedItem={this.props.selectedItem}
            searchLabel={gettext('Search Projects')}
            searchPlaceholder={gettext('Find project by name, code')}
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


var ProjectAdd = React.createClass({

  /* Layout */

  render: function () {
    return (
      <div className="item-add">
        <div className="hd">
          <h2>{gettext('Add Project')}</h2>
          <button
            onClick={this.props.handleCancel}
            className="btn btn-primary">{gettext('Cancel')}</button>
        </div>
        <div className="bd">
          <ProjectForm
            model={new this.props.model()}
            collection={this.props.collection}
            handleSuccess={this.props.handleSuccess} />
        </div>
      </div>
    );
  }

});


var ProjectEdit = React.createClass({

  /* Layout */

  render: function () {
    return (
      <div className="item-edit">
        <div className="hd">
          <h2>{gettext('Edit Project')}</h2>
          <button
            onClick={this.props.handleAdd}
            className="btn btn-primary">{gettext('Add Project')}</button>
        </div>
        <div className="bd">
        {!this.props.model ?
          <p>{gettext('Use the search form to find the project, then click on a project to edit.')}</p> :
          <ProjectForm
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
  App: ProjectsAdmin,
  model: models.Project,
  collection: models.ProjectSet,
};

