/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';
import ReactDOM from 'react-dom';

import UserEvent from 'components/UserEvent';
import { User } from 'models/user';

import UserProfileEdit from './components/UserProfileEdit';


window.PTL = window.PTL || {};


PTL.user = {

  init(opts) {
    if (opts.userData !== undefined) {
      const editButton = document.querySelector('.js-user-profile-edit');

      const user = new User(opts.userData, { urlRoot: l('/xhr/users/') });
      const props = {
        user,
        appRoot: opts.appRoot,
      };
      ReactDOM.render(<UserProfileEdit {...props} />, editButton);

      // FIXME: let's make the whole profile page a component, so a lot of the
      // boilerplate here is rendered redundant
      const popupBtns = document.querySelectorAll('.js-popup-tweet');
      [...popupBtns].map((btn) => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();

          const width = 500;
          const height = 260;
          const left = (screen.width / 2) - (width / 2);
          const top = (screen.height / 2) - (height / 2);
          window.open(e.currentTarget.href, '_blank',
                      `width=${width},height=${height},left=${left},top=${top}`);
        });
        return true;
      });
    }

    const lastActivity = document.querySelector('.js-last-action');
    const data = opts.lastEvent;
    const props = {
      checkName: data.check_name,
      checkDisplayName: data.check_display_name,
      displayName: data.displayname,
      email: data.email,
      displayDatetime: data.display_datetime,
      isoDatetime: data.iso_datetime,
      type: data.type,
      translationActionType: data.translation_action_type,
      unitSource: data.unit_source,
      unitUrl: data.unit_url,
      username: data.username,
    };
    ReactDOM.render(<UserEvent {...props} />, lastActivity);
  },

};
