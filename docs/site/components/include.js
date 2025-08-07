// Simple component loader for header and footer
function includeHTML() {
    const elementsWithInclude = document.querySelectorAll('[data-include]');
    
    elementsWithInclude.forEach(async (element) => {
        const file = element.getAttribute('data-include');
        if (file) {
            try {
                const response = await fetch(file);
                if (response.ok) {
                    const html = await response.text();
                    element.innerHTML = html;
                } else {
                    element.innerHTML = `<p>Error loading ${file}</p>`;
                }
            } catch (error) {
                element.innerHTML = `<p>Error loading ${file}</p>`;
            }
        }
    });
}

// Load components when page loads
document.addEventListener('DOMContentLoaded', includeHTML);