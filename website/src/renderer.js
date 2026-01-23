document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('githublink')
  const entryInput = document.getElementById('entrypoint')
  const frameworkInput = document.getElementById('framework')
  const runBtn = document.getElementById('runBtn')

  // scuffed validation checker
  function isValid(value) {
    if (!value) return false
    const v = value.trim()
    const ownerRepo = /^[^\/\s]+\/[^\/\s]+$/
    return ownerRepo.test(v) || v.toLowerCase().includes('github.com/')
  }

  input.addEventListener('input', () => {
    input.classList.remove('valid', 'invalid')
    if (input.value === '') return
    input.classList.add(isValid(input.value) ? 'valid' : 'invalid')
  })

  function updateRunButtonState() {
    const repoValid = isValid(input.value.trim())
    const filled = allFieldsFilled()
    runBtn.disabled = !(repoValid && filled)
  }

  // update run button state when any field changes
  input.addEventListener('input', () => updateRunButtonState())
  entryInput.addEventListener('input', () => updateRunButtonState())
  frameworkInput.addEventListener('input', () => updateRunButtonState())

  // initial state
  updateRunButtonState()

  // don't auto-submit on single-field change — require all fields and Run button

  function allFieldsFilled() {
    return (
      input.value.trim() !== '' &&
      entryInput.value.trim() !== '' &&
      frameworkInput.value.trim() !== ''
    )
  }

  // submit when Enter is pressed and all fields are filled
  [input, entryInput, frameworkInput].forEach(el => {
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        if (!allFieldsFilled()) return
        runBtn.click()
      }
    })
  })
  
  function gatherArgs() {
    return {
      repo_link: document.getElementById('githublink').value.trim(),
      entry_point_path: document.getElementById('entrypoint').value.trim(),
      framework: document.getElementById('framework').value.trim()
    }
  }

  runBtn.addEventListener('click', () => {
    const args = gatherArgs()
    // basic validation for repo
    if (!isValid(args.repo_link)) {
      input.classList.add('invalid')
      return
    }
    clearError()
    // disable inputs while running
    setInputsDisabled(true)
    window.API.setName(args)
  })

  // receive errors from main process
  if (window.API && window.API.onError) {
    window.API.onError((msg) => {
      showError(msg)
      setInputsDisabled(false)
    })
  }

  function showError(msg) {
    const box = document.getElementById('errorBox')
    if (!box) return
    box.textContent = `Error: ${msg}. Please try again.`
    box.style.display = 'block'
  }

  function clearError() {
    const box = document.getElementById('errorBox')
    if (!box) return
    box.textContent = ''
    box.style.display = 'none'
  }

  function setInputsDisabled(disabled) {
    input.disabled = disabled
    entryInput.disabled = disabled
    frameworkInput.disabled = disabled
    runBtn.disabled = disabled
    if (disabled) runBtn.classList.add('disabled')
    else runBtn.classList.remove('disabled')
  }
})