/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import 'imports?Backbone=>require("backbone")!backbone-move';

import $ from 'jquery';

import React from 'react';
import ReactDOM from 'react-dom';

import { q } from 'utils/dom';

import AdminController from './components/AdminController';
import User from './components/User';
import Language from './components/Language';
import Project from './components/Project';
import AdminRouter from './AdminRouter';


window.PTL = window.PTL || {};

const itemTypes = {
  user: User,
  language: Language,
  project: Project,
};

PTL.userAdmin = {
  init() {
    $(document).ready(() => {
      const processResults = (data) => {
        const results = {
          results: $.map(data.items.results, (result) => {
            const item = {
              id: result.id,
              text: result.text,
            };
            return item;
          }),
        };
        results.pagination = { more: data.items.more_results };
        return results;
      };
      $('.js-s2-new-members').on(
	's2-process-data', (evt, data) => PTL.s2.processData(data));
      $('.js-s2-new-members').on(
	's2-process-results', (evt, results) => processResults(results));
      $('.js-s2-new-members').on(
	's2-template-result', (evt, result) => PTL.s2.templateResult(result));
    });
  },
};

PTL.admin = {

  init(opts) {
    if (!itemTypes.hasOwnProperty(opts.itemType)) {
      throw new Error('Invalid `itemType`.');
    }

    ReactDOM.render(
      <AdminController
        adminModule={itemTypes[opts.itemType]}
        appRoot={opts.appRoot}
        formChoices={opts.formChoices || {}}
        router={new AdminRouter()}
      />,
      q('.js-admin-app')
    );
  },

};
