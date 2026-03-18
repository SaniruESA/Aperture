// preload.js - interactor between main and renderer scripts
// Provides API for function callbacks
const {contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('API', {
    setName: (args) => ipcRenderer.invoke('run-edit-all', args),
    onError: (cb) => {
        // register callback for app errors
        ipcRenderer.on('app-error', (_event, message) => {
            try { cb(message) } catch (e) { /* swallow */ }
        })
    }
    ,
    onLinks: (cb) => {
        ipcRenderer.on('app-links', (_e, links) => { try { cb(links) } catch (e) {} })
    },
    onAuthCode: (cb) => {
        ipcRenderer.on('auth-code', (_e, code) => { try { cb(code) } catch (e) {} })
    },
    onDone: (cb) => {
        ipcRenderer.on('done-link', (_e, url) => { try { cb(url) } catch (e) {} })
    },
    onProgess: (cb) => ipcRenderer.on('progress', (_e, msg) => cb(msg))
});

// allow renderer to request last done link synchronously via invoke
contextBridge.exposeInMainWorld('InternalAPI', {
    getLastDoneLink: () => ipcRenderer.invoke('get-last-done-link')
})