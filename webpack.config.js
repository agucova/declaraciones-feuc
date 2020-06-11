const path = require('path');

module.exports = {
    entry: './js/upload.js',
    output: {
        filename: 'upload.js',
        path: path.resolve(__dirname, 'declaraciones_feuc/static/'),
    },
};