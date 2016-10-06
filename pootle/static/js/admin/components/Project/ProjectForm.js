/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import FormElement from 'components/FormElement';
import ModelFormMixin from 'mixins/ModelFormMixin';

import ItemDelete from '../ItemDelete';


const ProjectForm = React.createClass({

  propTypes: {
    collection: React.PropTypes.object.isRequired,
    onDelete: React.PropTypes.func,
    onSuccess: React.PropTypes.func.isRequired,
  },

  mixins: [ModelFormMixin],

  fields: ['code', 'fullname', 'checkstyle', 'filetypes', 'treestyle',
           'source_language', 'ignoredfiles', 'report_email',
           'screenshot_search_prefix', 'disabled'],


  /* Handlers */

  handleSuccess(model) {
    this.props.onSuccess(model);
  },


  /* Layout */

  render() {
    const model = this.getResource();
    const { errors } = this.state;
    const { formData } = this.state;

    return (
      <form
        method="post"
        id="item-form"
        onSubmit={this.handleFormSubmit}
      >
        <div className="fields">
          <FormElement
            autoFocus
            disabled={model.hasOwnProperty('id')}
            label={gettext('Code')}
            handleChange={this.handleChange}
            name="code"
            errors={errors.code}
            value={formData.code}
          />
          <FormElement
            label={gettext('Full Name')}
            handleChange={this.handleChange}
            name="fullname"
            errors={errors.fullname}
            value={formData.fullname}
          />
          <FormElement
            type="select"
            clearable={false}
            options={model.getFieldChoices('checkstyle')}
            label={gettext('Quality Checks')}
            handleChange={this.handleChange}
            name="checkstyle"
            errors={errors.checkstyle}
            value={formData.checkstyle}
          />
          <FormElement
            type="select"
            multiple
            clearable={false}
            options={model.getFieldChoices('filetypes')}
            label={gettext('File types')}
            handleChange={this.handleChange}
            name="filetypes"
            errors={errors.filetypes}
            value={formData.filetypes}
          />
          <FormElement
            type="select"
            clearable={false}
            options={model.getFieldChoices('treestyle')}
            label={gettext('Project Tree Style')}
            handleChange={this.handleChange}
            name="treestyle"
            errors={errors.treestyle}
            value={formData.treestyle}
          />
          <FormElement
            type="select"
            clearable={false}
            options={model.getFieldChoices('source_language')}
            label={gettext('Source Language')}
            handleChange={this.handleChange}
            name="source_language"
            errors={errors.source_language}
            value={formData.source_language}
          />
          <FormElement
            label={gettext('Ignore Files')}
            handleChange={this.handleChange}
            name="ignoredfiles"
            errors={errors.ignoredfiles}
            value={formData.ignoredfiles}
          />
          <FormElement
            type="email"
            label={gettext('String Errors Contact')}
            handleChange={this.handleChange}
            name="report_email"
            errors={errors.report_email}
            value={formData.report_email}
          />
          <FormElement
            label={gettext('Screenshot Search Prefix')}
            handleChange={this.handleChange}
            name="screenshot_search_prefix"
            errors={errors.screenshot_search_prefix}
            value={formData.screenshot_search_prefix}
          />
          <FormElement
            type="checkbox"
            label={gettext('Disabled')}
            handleChange={this.handleChange}
            name="disabled"
            errors={errors.disabled}
            value={!!formData.disabled}
          />
        </div>
        <div className="buttons">
          <input type="submit" className="btn btn-primary"
            disabled={!this.state.isDirty}
            value={gettext('Save')}
          />
        {model.id &&
          <ul className="action-links">
            <li><a href={model.getAbsoluteUrl()}>{gettext('Overview')}</a></li>
            <li><a href={model.getLanguagesUrl()}>{gettext('Languages')}</a></li>
            <li><a href={model.getPermissionsUrl()}>{gettext('Permissions')}</a></li>
         {model.attributes.treestyle === 'pootle_fs' &&
          <li><a href={model.getFSUrl()}>{gettext('Filesystems')}</a></li>}
          </ul>}
        </div>
      {this.props.onDelete &&
        <div>
          <p className="divider" />
          <div className="buttons">
            <ItemDelete item={model} onDelete={this.props.onDelete} />
          </div>
        </div>}
      </form>
    );
  },

});


export default ProjectForm;
