// main.js - Electron main process
// This class creates the main UI window and initializes the accompanying python process, as well
// as handling all requests from the UI and python script (opens external URLs when necessary).
// The functionality of this class was tested through verification that external links were opened in browser 
// window and through end-to-end testing on the entire UI system.
const { app, BrowserWindow, ipcMain, shell } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const fs = require('fs')

let pythonProcess = null
let pythonStarting = false
let mainWindow = null
let lastDoneLink = null
function startPythonProcess() {
  if (pythonProcess && !pythonProcess.killed && pythonProcess.exitCode === null) return
  pythonStarting = true

  let cmd, args
  if (app.isPackaged) {
    const resources = process.resourcesPath
    if (process.platform === 'darwin') {
      cmd = path.join(resources, 'python', 'mac', 'Aperture')
    } else if (process.platform === 'win32') {
      cmd = path.join(resources, 'python', 'Aperture.exe')
    } else {
      cmd = path.join(resources, 'python', 'Aperture')
    }
    args = []
    if (!fs.existsSync(cmd)) {
      console.error('Packaged helper not found at', cmd)
      pythonStarting = false
      return
    }
  } else {
    const pythonExe = path.resolve(__dirname, '..', '..', '.venv', 'bin', 'python3')
    const scriptPath = path.resolve(__dirname, '..', '..', 'code_modification', 'main.py')
    cmd = fs.existsSync(pythonExe) ? pythonExe : 'python3'
    args = [scriptPath]
    if (!fs.existsSync(scriptPath)) {
      console.warn('Dev script not found at', scriptPath)
    }
  }

  try {
    pythonProcess = spawn(cmd, args, {
      cwd: path.resolve(__dirname, '..', '..'),
      stdio: ['pipe', 'pipe', 'pipe'],
    })
  } catch (err) {
    console.error('Failed to spawn python helper:', err)
    pythonStarting = false
    return
  }

  console.log('Spawned python helper', { cmd, args, pid: pythonProcess.pid })
  pythonStarting = false

  pythonProcess.stdout.setEncoding('utf8')
  pythonProcess.stdout.on('data', chunk => {
    chunk.toString().split(/\r?\n/).filter(Boolean).forEach(line => {
      console.log(`[PYTHON stdout] ${line}`)
      try {
        const obj = JSON.parse(line)
        // open external URLs (OAuth)
        if (obj.action === 'open_url' && obj.url) {
          // open externally and forward to renderer (and remember for late requests)
          shell.openExternal(obj.url)
          lastDoneLink = obj.url
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('done-link', obj.url)
          }
          return
        }
        // progress messages forwarded to renderer
        if (obj.action === 'progress' && obj.text) {
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('progress', obj.text)
          }
          return
        }
        // completed run -> load done page
        if (obj.status === 'ok' && obj.action === 'run_edit_all') {
          if (mainWindow && !mainWindow.isDestroyed()) {
            const donePath = path.join(__dirname, '..', 'pages', 'done.html')
            const fallback = path.join(__dirname, '..', 'done.html')
            const loadFile = fs.existsSync(donePath) ? donePath : fallback
            mainWindow.loadFile(loadFile).catch(err => console.error('Failed to load done page', err))
          }
          return
        }
        // error from python
        if (obj.status === 'error') {
          showError(obj.error || 'unknown python error')
        }
      } catch (e) {
        // not JSON - ignore or forward raw slines as progress
        if (mainWindow && !mainWindow.isDestroyed()) {
          mainWindow.webContents.send('progress', line)
        }
      }
    })
  })

  pythonProcess.stderr.setEncoding('utf8')
  pythonProcess.stderr.on('data', chunk => {
    chunk.toString().split(/\r?\n/).filter(Boolean).forEach(line => {
      console.error(`[PYTHON stderr] ${line}`)
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('progress', `ERROR: ${line}`)
      }
    })
  })

  pythonProcess.on('error', err => {
    console.error('Python process error:', err)
  })

  pythonProcess.on('close', code => {
    console.log(`Python process exited with code ${code}`)
  })
}

function ensurePythonReady(timeout = 3000) {
  return new Promise((resolve, reject) => {
    if (pythonProcess && !pythonProcess.killed && pythonProcess.exitCode === null && pythonProcess.stdin && pythonProcess.stdin.writable) {
      return resolve()
    }
    if (pythonStarting) {
      const t = setTimeout(() => reject(new Error('python start timeout')), timeout)
      const check = setInterval(() => {
        if (pythonProcess && pythonProcess.stdin && pythonProcess.stdin.writable && pythonProcess.exitCode === null) {
          clearTimeout(t); clearInterval(check); return resolve()
        }
        if (pythonProcess && pythonProcess.exitCode !== null) {
          clearTimeout(t); clearInterval(check); return reject(new Error('python exited'))
        }
      }, 150)
      return
    }
    startPythonProcess()
    const t = setTimeout(() => reject(new Error('python start timeout')), timeout)
    const check = setInterval(() => {
      if (pythonProcess && pythonProcess.stdin && pythonProcess.stdin.writable && pythonProcess.exitCode === null) {
        clearTimeout(t); clearInterval(check); return resolve()
      }
      if (pythonProcess && pythonProcess.exitCode !== null) {
        clearTimeout(t); clearInterval(check); return reject(new Error('python exited'))
      }
    }, 150)
  })
}

ipcMain.handle('run-edit-all', async (_event, params) => {
  try {
    await ensurePythonReady()
    // show loading page
    if (mainWindow && !mainWindow.isDestroyed()) {
      const loadingPath = path.join(__dirname, '..', 'pages', 'loading.html')
      const fallback = path.join(__dirname, '..', 'loading.html')
      const loadFile = fs.existsSync(loadingPath) ? loadingPath : fallback
      await mainWindow.loadFile(loadFile).catch(err => console.error('Failed to load loading page', err))
    }

    if (!pythonProcess || !pythonProcess.stdin || !pythonProcess.stdin.writable) {
      throw new Error('Python stdin not writable')
    }

    pythonProcess.stdin.write(JSON.stringify({ action: 'run_edit_all', ...params }) + '\n')
    return { status: 'sent' }
  } catch (err) {
    console.error('Failed to send to python:', err)
    await showError(String(err))
    return { status: 'error', message: String(err) }
  }
})
async function showError(msg) {                                                                                                  
  if (!mainWindow || mainWindow.isDestroyed()) return
  try {                                                                                                                                 
    await mainWindow.loadFile(path.join(__dirname, '..', 'index.html'))
    if (mainWindow && !mainWindow.isDestroyed()) {                                                                                      
      mainWindow.webContents.send('app-error', msg)                                                                                     
    }
  } catch (_) {}                                                                                                                        
}        

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1000,
    height: 720,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    }
  })

  const idx = path.join(__dirname, '..', 'index.html')
  mainWindow.loadFile(idx).catch(err => console.error('Failed to load index.html', err))
}

app.whenReady().then(() => {
  startPythonProcess()
  createWindow()

  // Provide renderer a way to request the last done link (if it missed the event)
  ipcMain.handle('get-last-done-link', async () => {
    return lastDoneLink
  })

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  try { if (pythonProcess && !pythonProcess.killed) pythonProcess.kill() } catch (_) {}
  if (process.platform !== 'darwin') app.quit()
})