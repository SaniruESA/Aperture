const { app, BrowserWindow, ipcMain } = require('electron')
const { spawn } = require('child_process')
const path = require('path')

let pythonProcess
let mainWindow

function startPythonProcess() {
  // absolute path to script in repo
  const pythonPath = path.resolve(__dirname, '..', '..', 'code_modification', 'main.py')
  pythonProcess = spawn('python3', [pythonPath], {
    cwd: path.resolve(__dirname, '..', '..'), // repo root so relative paths work
    stdio: ['pipe', 'pipe', 'pipe']
  })

  pythonProcess.stdout.setEncoding('utf8')
  pythonProcess.stdout.on('data', chunk => {
    // Just testing from python output stream for now
    chunk.toString().split(/\r?\n/).filter(Boolean).forEach(line => {
      console.log(`[python stdout] ${line}`)
      try {
        const obj = JSON.parse(line)
        if (obj.status === 'ok' && obj.action === 'run_edit_all') {
          if (mainWindow && !mainWindow.isDestroyed()) {
            // load done.html from website pages
            mainWindow.loadFile(path.join(__dirname, '..', 'done.html'))
          }
        }

      } catch (e) {
      
      }
    })
  })

  pythonProcess.stderr.setEncoding('utf8')
  pythonProcess.stderr.on('data', chunk => {
    chunk.toString().split(/\r?\n/).filter(Boolean).forEach(line => {
      console.error(`[python error] ${line}`)
    })
  })

  pythonProcess.on('error', err => {
    console.error('error:', err)
  })

  pythonProcess.on('close', code => {
    console.log(`Python exited with code ${code}`)
  })
}

ipcMain.handle("run-edit-all", async (_event, params) => {
  try {
    if (!pythonProcess || pythonProcess.killed || pythonProcess.exitCode !== null) startPythonProcess()
    pythonProcess.stdin.write(JSON.stringify({ action: "run_edit_all", ...params }) + "\n")
    return { status: 'sent' }
  } catch (err) {
  }
})

const createWindow = () => {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    }
  })

  mainWindow.loadFile('index.html')
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

