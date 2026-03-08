const { app, BrowserWindow, ipcMain } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const os = require('os')
const fs = require('fs')

let pythonProcess
let mainWindow
let lastParams = null
// Buffers for messages coming from the python child while different pages are shown
let bufferedLinks = []
let bufferedAuthCodes = []
let bufferedDoneLink = null
let lastSentDoneLink = null

// By default, execute any bundled PyInstaller executables found under resources
const ALLOW_BUNDLED_EXE = true

// Use temp folders for Electron profile and cache to avoid Windows error
const tmpUserData = path.join(os.tmpdir(), 'ApertureUserData')
const tmpCache = path.join(os.tmpdir(), 'ApertureCache')
try {
  fs.mkdirSync(tmpUserData, { recursive: true })
  fs.mkdirSync(tmpCache, { recursive: true })
} catch (e) {
  // Ignore directory creation errors
}

// Set paths before app.whenReady()
try {
  app.setPath('userData', tmpUserData)
  app.commandLine.appendSwitch('disk-cache-dir', tmpCache)
} catch (e) {
  // If app isn't initialized yet or this fails, ignore and continue
}

// Helper to construct GH repo URL
function makeRepoUrl(repo) {
  if (!repo) return null
  const v = repo.trim()
  if (v.includes('github.com')) return v
  const ownerRepo = /^[^\/\s]+\/[^\/\s]+$/
  if (ownerRepo.test(v)) return `https://github.com/${v}`
  return null
}

function startPythonProcess() {
  // Determine what to run:
  // - during development: run the local Python script
  // - when packaged: prefer a bundled python executable (pyinstaller) if present under resources,
  //   otherwise look for an unpacked "code_modification/main.py" in "resources"
  const devPythonPath = path.resolve(__dirname, '..', '..', 'code_modification', 'main.py')
  const candidates = []

  if (!app.isPackaged) {
    // During development prefer a locally-built one-file exe if present (useful for testing PyInstaller build)
    const devExe = path.join(__dirname, '..', 'build', 'python', 'win', 'Aperture.exe')
    if (fs.existsSync(devExe)) {
      candidates.push({ type: 'exe', cmd: devExe, args: [], cwd: path.resolve(__dirname, '..') })
    }
    candidates.push({ type: 'pyfile', cmd: process.env.PYTHON || 'python', args: [devPythonPath], cwd: path.resolve(__dirname, '..', '..') })
} else {
    // Places inside resources when packaged
    const r = process.resourcesPath

    // Prioritize bundled PyInstaller exes first
    if (ALLOW_BUNDLED_EXE) {
      candidates.push({ type: 'exe', cmd: path.join(r, 'python', 'win', 'Aperture.exe'), args: [], cwd: r })
      candidates.push({ type: 'exe', cmd: path.join(r, 'python', 'win', 'aperture', 'Aperture.exe'), args: [], cwd: r })
    }
    // Fallback to unpacked script
    candidates.push({ type: 'pyfile', cmd: process.env.PYTHON || 'python', args: [path.join(r, 'code_modification', 'main.py')], cwd: r })
  }
  
  // Find the first candidate that exists (for exe or pyfile path)
  let chosen = null
  for (const c of candidates) {
    try {
      if (c.type === 'exe' || (c.type === 'pyfile' && c.args && c.args[0])) {
        const p = c.type === 'exe' ? c.cmd : c.args[0]
        if (fs.existsSync(p)) { chosen = c; break }
      }
    } catch (e) {}
  }

  if (!chosen) {
    // Fallback: try invoking system python on packaged app path
    const fallback = path.join(process.resourcesPath, 'code_modification', 'main.py')
    chosen = { type: 'pyfile', cmd: process.env.PYTHON || 'python', args: [fallback], cwd: process.resourcesPath }
  }

  // Log what we're about to start so packaged/runtime diagnostics are visible
  try {
    console.log('[python runner] chosen candidate:', chosen)
  } catch (e) {}

  pythonProcess = spawn(chosen.cmd, chosen.args, { cwd: chosen.cwd, stdio: ['pipe', 'pipe', 'pipe'], env: { ...process.env, PYTHONUNBUFFERED: '1' } })

  pythonProcess.stdout.setEncoding('utf8')
  pythonProcess.stdout.on('data', chunk => {

    // Just testing from python output stream for now
    chunk.toString().split(/\r?\n/).filter(Boolean).forEach(line => {
      console.log(`[python stdout] ${line}`)
      try {
        const obj = JSON.parse(line)

        // Handle structured messages from python
        if (obj.action === 'run_edit_all' && obj.status === 'ok') {
          if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.loadFile(path.join(__dirname, '..', 'pages', 'done.html'))
          }
        }

        if (obj.action === 'open_url' && obj.url) {
          // If the URL points to a local html file, prefer loading it via loadFile
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

              // Find candidate locations inside the app (pages/ or root)
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

          // Decide whether to send now or buffer depending on which page is visible
          try {
            if (mainWindow && !mainWindow.isDestroyed()) {
              const current = mainWindow.webContents.getURL() || ''
              if (current.includes('done.html')) {
                mainWindow.webContents.send('done-link', obj.url)
                lastSentDoneLink = obj.url
              } else if (current.includes('index.html')) {
                mainWindow.webContents.send('app-links', [obj.url])
              } else {
                // buffer for later (either index or done)
                // if this looks like a PR URL, prefer the done-link buffer
                if (obj.url.includes('/pull/')) bufferedDoneLink = obj.url
                else bufferedLinks.push(obj.url)
              }

            } else {
              // No window yet, buffer
              if (obj.url.includes('/pull/')) bufferedDoneLink = obj.url
              else bufferedLinks.push(obj.url)
            }
            
          } catch (e) {
            // fallback: send as app-links
            if (mainWindow && !mainWindow.isDestroyed()) mainWindow.webContents.send('app-links', [obj.url])
            else bufferedLinks.push(obj.url)
          }
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

  // When any page finishes loading, flush buffered messages if we're on index.html
  mainWindow.webContents.on('did-finish-load', () => {
    try {
      const url = mainWindow.webContents.getURL() || ''
      // flush for index.html
      if (url.endsWith('index.html') || url.includes('index.html')) {
        if (bufferedLinks.length) {
          mainWindow.webContents.send('app-links', bufferedLinks)
          bufferedLinks = []
        }
        if (bufferedAuthCodes.length) {
          const last = bufferedAuthCodes[bufferedAuthCodes.length-1]
          mainWindow.webContents.send('auth-code', last)
          bufferedAuthCodes = []
        }
      }
      // flush for done.html
      if (url.endsWith('done.html') || url.includes('done.html')) {
        if (bufferedDoneLink) {
          mainWindow.webContents.send('done-link', bufferedDoneLink)
          lastSentDoneLink = bufferedDoneLink
          bufferedDoneLink = null
        }
        // also send any links that aren't PRs
        if (bufferedLinks.length) {
          mainWindow.webContents.send('app-links', bufferedLinks)
          bufferedLinks = []
        }
      }
    } catch (e) {
      // ignore
    }
  })
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

// allow renderer to request last done link
ipcMain.handle('get-last-done-link', async () => {
  return lastSentDoneLink || bufferedDoneLink || null
})

app.on('window-all-closed', () => {
  if (pythonProcess && !pythonProcess.killed) {
    try { pythonProcess.kill() } catch (_) {}
  }
  if (process.platform !== 'darwin') app.quit()
})

