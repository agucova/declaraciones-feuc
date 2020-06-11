const Uppy = require('@uppy/core')
const Dashboard = require('@uppy/dashboard')
const FileInput = require('@uppy/file-input')
const GoogleDrive = require('@uppy/google-drive')
const Url = require('@uppy/url')
const spanishLocale = require('@uppy/locales/lib/es_ES')

const uppy = Uppy({
    id: 'uppy',
    autoProceed: true,
    allowMultipleUploads: false,
    debug: true,
    restrictions: {
        maxFileSize: 20970000,
        allowedFileTypes: ["application/pdf"]
    },
    onBeforeFileAdded: (currentFile, files) => currentFile,
    onBeforeUpload: (files) => {},
    locale: spanishLocale
})

uppy.use(Dashboard, {
    inline: true,
    target: '#uploader',
    showProgressDetails: true,
    width: "100%",
    height: "350px",
    note: 'Solo PDFs de hasta 20 mb.'
})
uppy.use(GoogleDrive, {
    target: Dashboard,
    companionUrl: '/' // TODO: #6 Set a companion URL
})
uppy.use(Url, {
    target: Dashboard,
    companionUrl: '/'
})