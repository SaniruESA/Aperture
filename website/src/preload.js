const {contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('API', {
    setName: (args) => ipcRenderer.invoke('run-edit-all', args),
    onError: (cb) => {
        // register callback for app errors
        ipcRenderer.on('app-error', (_event, message) => {
            try { cb(message) } catch (e) { /* swallow */ }
        })
    }
});