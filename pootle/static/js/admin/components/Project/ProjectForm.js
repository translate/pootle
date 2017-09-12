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

  fields: ['code', 'fullname', 'checkstyle', 'filetypes', 'fs_plugin',
           'fs_url', 'fs_mapping', 'template_name', 'source_language', 'ignoredfiles',
           'report_email', 'screenshot_search_prefix', 'disabled'],

  /* Handlers */

  handleSuccess(model) {
    this.props.onSuccess(model);
  },

  handleCodeChange(e) {
    if (e.target.name === 'code') {
      const formData = this.state.formData;
      if (formData.fs_plugin === 'localfs') {
        const localfsPrefix = '{POOTLE_TRANSLATION_DIRECTORY}';
        const urlsToUpdate = ['', [localfsPrefix, this.state.formData.code].join('')];

        if (urlsToUpdate.indexOf(formData.fs_url) !== -1) {
          formData.code = e.target.value;
          formData.fs_url = [localfsPrefix, e.target.value].join('');
          this.setState({ formData });
        }
      }
    }
  },

  handlePresetChange(mapping) {
    const formData = this.state.formData;
    formData.fs_mapping = mapping;
    this.setState({ formData });
  },

  /* Layout */

  render() {
    const model = this.getResource();
    const { errors } = this.state;
    const { formData } = this.state;
    const presets = model.getFieldChoices('fs_preset');
    let fsPreset = 'Custom';
    for (let i = 0; i < presets.length; i++) {
      const preset = presets[i];
      if (preset.value === formData.fs_mapping) {
        fsPreset = preset.label;
      }
    }
    return (
      <form
        method="post"
        id="item-form"
        onChange={this.handleCodeChange}
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
            options={model.getFieldChoices('fs_plugin')}
            label={gettext('Filesystem backend')}
            handleChange={this.handleChange}
            name="fs_plugin"
            errors={errors.fs_plugin}
            value={formData.fs_plugin}
          />
          <FormElement
            label={gettext('Path or URL')}
            handleChange={this.handleChange}
            name="fs_url"
            errors={errors.fs_url}
            value={formData.fs_url}
          />
          <FormElement
            type="select"
            clearable={false}
            options={model.getFieldChoices('fs_preset')}
            label={gettext('Path mapping preset')}
            onChange={this.handlePresetChange}
            name="fs_preset"
            value={fsPreset}
          />
          <FormElement
            label={gettext('Path mapping')}
            handleChange={this.handleChange}
            name="fs_mapping"
            errors={errors.fs_mapping}
            value={formData.fs_mapping}
          />
          <FormElement
            label={gettext('Template name')}
            handleChange={this.handleChange}
            name="template_name"
            errors={errors.template_name}
            value={formData.template_name}
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
