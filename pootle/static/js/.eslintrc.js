module.exports = {
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
  },
  plugins: [
    'react',
  ],
  rules: {
    'quotes': [2, 'single', 'avoid-escape'],
  },
};
