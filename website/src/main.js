const { app, BrowserWindow, ipcMain } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

let pythonProcess

function startPythonProcess() {
  //relative path to github editing script
  const pythonPath = path.join(__dirname, '..', '..', 'code_modification', 'main.py')
  pythonProcess = spawn('python3', [pythonPath], {
    cwd: path.join(__dirname, '..'),
    stdio: ['pipe', 'pipe', 'pipe'] // displaying errors not added yet
  })
}

ipcMain.handle("run-edit-all", async (_event, params) => {
  pythonProcess.stdin.write(JSON.stringify({ action: "run_edit_all",...params }) + "\n")
})

const createWindow = () => {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    }
  })

  win.loadFile('index.html')
}

app.whenReady().then(() => {
  startPythonProcess()
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  if (pythonProcess && !pythonProcess.killed) {
    try { pythonProcess.kill() } catch (_) {}
  }
  if (process.platform !== 'darwin') app.quit()
})

