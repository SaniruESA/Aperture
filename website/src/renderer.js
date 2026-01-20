const src = document.getElementById('githublink')

function handleOnChange({ target: { value }}) {
    window.API.setName(value);
}
src.addEventListener('change', handleOnChange);