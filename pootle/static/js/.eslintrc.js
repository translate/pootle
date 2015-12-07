module.exports = {
  'extends': 'airbnb',
  env: {
    browser: true,
    es6: true,
  },
  ecmaFeatures: {
    jsx: true,
    modules: true,
  },
  globals: {
    gettext: false,
    ngettext: false,
    interpolate: false,
    l: false,
    PTL: false,
    require: false,
    shortcut: false,
    sorttable: false,
  },
  plugins: [
    'react',
  ],
};
