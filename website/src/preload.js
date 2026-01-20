const {contextBridge, ipcRenderer } = require('electron'); 
contextBridge.exposeInMainWorld('API', {
    setName: (args) => {
        ipcRenderer.invoke('run-edit-all', args)
    }
});