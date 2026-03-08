// Upon DOM loading, takes input from HTML page
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('githublink')
  const entryInput = document.getElementById('entrypoint')
  const frameworkInput = document.getElementById('framework')
  const runBtn = document.getElementById('runBtn')

  // Validation checker for input link
  // args: value - String to test regex against
  function isValid(value) {
    if (!value) return false
    const v = value.trim()
    // regex used to verify if the input is in owner/repo format
    const ownerRepo = /^[^\/\s]+\/[^\/\s]+$/
    return ownerRepo.test(v) || v.toLowerCase().includes('github.com/') // also checks if it is a github link seperately
  }
  // 
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

  // simple check for all input fields being filled out, true if this is the case, 
  // false otherwise
  function allFieldsFilled() {
    return (
      input.value.trim() !== '' &&
      entryInput.value.trim() !== '' &&
      frameworkInput.value.trim() !== ''
    )
  }

  // For each input field, add an event listener for the enter keypress
  [input, entryInput, frameworkInput].forEach(el => {
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        // Asserts that all required fields are filled before continuing 
        if (!allFieldsFilled()) return
        runBtn.click()
      }
    })
  })
  // Helper function to organize all the text field elements
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

  // receive extracted auth links
  if (window.API && window.API.onLinks) {
    window.API.onLinks((links) => {
      const box = document.getElementById('linksBox')
      if (!box) return
      box.innerHTML = ''
      links.forEach(u => {
        const a = document.createElement('a')
        a.href = u
        a.textContent = u
        a.target = '_blank'
        box.appendChild(a)
      })
      box.style.display = links.length ? 'block' : 'none'
    })
  }

  // receive auth code
  if (window.API && window.API.onAuthCode) {
    window.API.onAuthCode((code) => {
      const box = document.getElementById('authCodeBox')
      if (!box) return
      box.textContent = `Authentication code: ${code}`
      box.style.display = 'block'
      // make sure inputs are enabled so user can paste code
      setInputsDisabled(false)
    })
  }
  // Simple error handler with message
  function showError(msg) {
    const box = document.getElementById('errorBox')
    if (!box) return
    box.textContent = `Error: ${msg}. Please try again.`
    box.style.display = 'block'
  }
  // Clears the error message
  function clearError() {
    const box = document.getElementById('errorBox')
    if (!box) return
    box.textContent = ''
    box.style.display = 'none'
  }
  // Function to set all input fields to either enabled or disabled
  // args: disabled
  // true -> input disabled
  // false -> input enabled
  function setInputsDisabled(disabled) {
    input.disabled = disabled
    entryInput.disabled = disabled
    frameworkInput.disabled = disabled
    runBtn.disabled = disabled
    if (disabled) runBtn.classList.add('disabled')
    else runBtn.classList.remove('disabled')
  }
})