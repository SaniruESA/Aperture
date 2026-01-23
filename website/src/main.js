const { app, BrowserWindow, ipcMain } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const os = require('os')
const fs = require('fs')

let pythonProcess
let mainWindow
let lastParams = null

// Use writable temporary folders for Electron profile and cache to avoid
// "Unable to move the cache: Access is denied" errors on Windows.
const tmpUserData = path.join(os.tmpdir(), 'ApertureUserData')
const tmpCache = path.join(os.tmpdir(), 'ApertureCache')
try {
  fs.mkdirSync(tmpUserData, { recursive: true })
  fs.mkdirSync(tmpCache, { recursive: true })
} catch (e) {
  // ignore directory creation errors
}

// set paths before app.whenReady()
try {
  app.setPath('userData', tmpUserData)
  app.commandLine.appendSwitch('disk-cache-dir', tmpCache)
  // optionally disable GPU if GPU cache still causes issues
  // app.commandLine.appendSwitch('disable-gpu')
} catch (e) {
  // if app isn't initialized yet or this fails, ignore and continue
}

function makeRepoUrl(repo) {
  if (!repo) return null
  const v = repo.trim()
  if (v.includes('github.com')) return v
  const ownerRepo = /^[^\/\s]+\/[^\/\s]+$/
  if (ownerRepo.test(v)) return `https://github.com/${v}`
  return null
}

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
        // handle structured messages from python
        if (obj.action === 'run_edit_all' && obj.status === 'ok') {
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.loadFile(path.join(__dirname, '..', 'pages', 'done.html'))
          }
        }

        if (obj.action === 'open_url' && obj.url) {
          // if the URL points to a local html file, prefer loading it via loadFile
          try {
            const u = obj.url
            if (u.startsWith('file://') || u.endsWith('.html')) {
              let localPath
              if (u.startsWith('file://')) {
                // convert file:// URL to local path
                try {
                  const decoded = decodeURI(new URL(u).pathname)
                  // Windows paths may start with a leading slash
                  localPath = decoded.replace(/^\/+/, '')
                } catch (e) {
                  localPath = u.replace('file://', '')
                }
              } else {
                localPath = u
              }

              // find candidate locations inside the app (pages/ or root)
              const candidates = [
                path.join(__dirname, '..', 'pages', path.basename(localPath)),
                path.join(__dirname, '..', path.basename(localPath))
              ]
              let found = null
              for (const c of candidates) {
                try {
                  if (require('fs').existsSync(c)) { found = c; break }
                } catch (e) {}
              }
              if (found && mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.loadFile(found)
                return
              }
            }
          } catch (e) {
            // fallthrough to sending as external link
          }

          if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('app-links', [obj.url])
        }

        if (obj.action === 'auth_code' && obj.code) {
          if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('auth-code', obj.code)
        }

        if (obj.status === 'error') {
          const msg = obj.error || JSON.stringify(obj)
          console.error('[python reported error]', msg)
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.loadFile('index.html').then(() => {
              mainWindow.webContents.send('app-error', msg)
            }).catch(() => {
              mainWindow.webContents.send('app-error', msg)
            })
          }
        }

      } catch (e) {
        // non-json line from python — log and try to extract URLs / codes
        const text = line
        console.log('[python stdout non-json]', text)

        try {
          // extract urls
          const urlRegex = /(https?:\/\/[^\s"'<>]+)/g
          const urls = []
          let m
          while ((m = urlRegex.exec(text)) !== null) {
            urls.push(m[1])
          }
          if (urls.length && mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('app-links', urls)
          }

          // try to extract code from url query param or explicit code lines
          // look for code= in any of the urls
          for (const u of urls) {
            const q = u.split('?')[1]
            if (q) {
              const parts = q.split('&')
              for (const p of parts) {
                const [k, v] = p.split('=')
                if (k && k.toLowerCase() === 'code' && v) {
                  if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('auth-code', decodeURIComponent(v))
                }
              }
            }
          }

          // generic code detection (lines containing 'code:' or 'verification code')
          const codeMatch = text.match(/(?:code[:=]\s*|verification code[:=]\s*)([A-Za-z0-9\-_.]{4,40})/i)
          if (codeMatch && codeMatch[1] && mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.webContents.send('auth-code', codeMatch[1])
          }
        } catch (ee) {
          // ignore parsing errors
        }
      }
    })
  })

  pythonProcess.stderr.setEncoding('utf8')
  const stderrBuffer = []
  pythonProcess.stderr.on('data', chunk => {
    chunk.toString().split(/\r?\n/).filter(Boolean).forEach(line => {
      console.error(`[python error] ${line}`)
      // keep a rolling buffer of recent stderr lines for diagnostics
      stderrBuffer.push(line)
      if (stderrBuffer.length > 200) stderrBuffer.shift()
      if (mainWindow && !mainWindow.isDestroyed()) {
        try {
          // do not immediately navigate — surface as an error and let python exit/close decide
          mainWindow.webContents.send('app-error', line)
        } catch (_) {
          // swallow
        }
      }
    })
  })

  pythonProcess.on('error', err => {
    console.error('error:', err)
    if (mainWindow && !mainWindow.isDestroyed()) {
      try {
        mainWindow.loadFile('index.html').then(() => {
          mainWindow.webContents.send('app-error', String(err))
        }).catch(() => {
          mainWindow.webContents.send('app-error', String(err))
        })
      } catch (_) {}
    }
  })

  pythonProcess.on('close', code => {
    console.log(`Python exited with code ${code}`)
    if (code !== 0 && mainWindow && !mainWindow.isDestroyed()) {
      try {
        const msg = `Python exited with code ${code}. Recent stderr:\n${stderrBuffer.join('\n')}`
        mainWindow.loadFile('index.html').then(() => {
          mainWindow.webContents.send('app-error', msg)
        }).catch(() => {
          mainWindow.webContents.send('app-error', msg)
        })
      } catch (_) {}
    }
  })
}

ipcMain.handle("run-edit-all", async (_event, params) => {
  try {
    lastParams = params
    if (!pythonProcess || pythonProcess.killed || pythonProcess.exitCode !== null) startPythonProcess()

    if (!pythonProcess || !pythonProcess.stdin || !pythonProcess.stdin.writable) {
      throw new Error('could not write to python')
    }

    // show loading page immediately
    if (mainWindow && !mainWindow.isDestroyed()) {
      await mainWindow.loadFile(path.join(__dirname, '..', 'pages', 'loading.html')).catch(err => {
        console.error('Failed to load stuff', err)
      })
    }

    // send command to python
    pythonProcess.stdin.write(JSON.stringify({ action: "run_edit_all", ...params }) + "\n")
    return { status: 'sent' }
  } catch (err) {
    console.error('Failed to send to python:', err)
    if (mainWindow && !mainWindow.isDestroyed()) {
      try {
        mainWindow.loadFile('index.html').then(() => {
          mainWindow.webContents.send('app-error', String(err))
        }).catch(() => {
          mainWindow.webContents.send('app-error', String(err))
        })
      } catch (_) {}
    }
    return { status: 'error', message: String(err) }
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

