/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import Backbone from 'backbone';


const AdminRouter = Backbone.Router.extend({

  routes: {
    '?q=:searchQuery': 'main',
    '': 'main',
    ':id(/)': 'edit',
  },

});


export default AdminRouter;
