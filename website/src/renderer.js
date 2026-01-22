document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('githublink')

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

  function handleOnChange({ target: { value }}) {
      window.API.setName(value);
  }
  input.addEventListener('change', handleOnChange);
})