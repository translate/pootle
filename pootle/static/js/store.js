/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import { applyMiddleware, createStore } from 'redux';
import thunkMiddleware from 'redux-thunk';

import createReducer from './reducers';


const createStoreWithMiddleware = applyMiddleware(
  thunkMiddleware
)(createStore);


function configureStore() {
  return createStoreWithMiddleware(createReducer());
}


export default configureStore;
