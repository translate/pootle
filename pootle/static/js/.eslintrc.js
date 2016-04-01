module.exports = {
  'extends': 'airbnb',
  env: {
    browser: true,
  },
  parserOptions: {
    ecmaVersion: 6,
    ecmaFeatures: {
      jsx: true,
    },
    sourceType: 'module',
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
  rules: {
    'react/prefer-es6-class': 0,
    'react/prefer-stateless-function': 1,
  },
};
