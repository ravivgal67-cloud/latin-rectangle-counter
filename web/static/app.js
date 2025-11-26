// Latin Rectangle Counter - Frontend JavaScript

// API Configuration
const API_BASE_URL = window.location.origin;

// DOM Elements
let homeViewBtn, calcViewBtn, presentViewBtn;
let homeView, calculationView, presentationView;
let countForm, submitBtn;
let modeRadios, inputFields;
let progressIndicator, errorDisplay, resultsSection;
let resultsTbody;

// Results view elements
let emptyResultsState, resultsTableCard, presentationTbody;
let filterInputs, refreshBtn, clearFiltersBtn, exportCsvBtn, exportJsonBtn;
let currentSort = { column: 'n', direction: 'asc' };

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeElements();
    setupEventListeners();
});

/**
 * Initialize DOM element references
 */
function initializeElements() {
    // View switcher
    homeViewBtn = document.getElementById('home-view-btn');
    calcViewBtn = document.getElementById('calc-view-btn');
    presentViewBtn = document.getElementById('present-view-btn');
    
    // Views
    homeView = document.getElementById('home-view');
    calculationView = document.getElementById('calculation-view');
    presentationView = document.getElementById('presentation-view');
    
    // Form elements
    countForm = document.getElementById('count-form');
    submitBtn = document.getElementById('submit-btn');
    
    // Mode radios and input fields
    modeRadios = document.querySelectorAll('input[name="mode"]');
    inputFields = {
        single: document.getElementById('single-fields'),
        allN: document.getElementById('all-n-fields'),
        range: document.getElementById('range-fields')
    };
    
    // Status displays
    progressIndicator = document.getElementById('progress-indicator');
    errorDisplay = document.getElementById('error-display');
    resultsSection = document.getElementById('results-section');
    resultsTbody = document.getElementById('results-tbody');
    
    // Results view elements
    emptyResultsState = document.getElementById('empty-results-state');
    resultsTableCard = document.getElementById('results-table-card');
    presentationTbody = document.getElementById('presentation-tbody');
    filterInputs = document.querySelectorAll('.filter-input');
    refreshBtn = document.getElementById('refresh-btn');
    clearFiltersBtn = document.getElementById('clear-filters-btn');
    exportCsvBtn = document.getElementById('export-csv-btn');
    exportJsonBtn = document.getElementById('export-json-btn');
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // View switcher
    homeViewBtn.addEventListener('click', () => switchView('home'));
    calcViewBtn.addEventListener('click', () => switchView('calculation'));
    presentViewBtn.addEventListener('click', () => switchView('presentation'));
    
    // Get started button
    const getStartedBtn = document.getElementById('get-started-btn');
    if (getStartedBtn) {
        getStartedBtn.addEventListener('click', () => switchView('calculation'));
    }
    
    // Mode tabs
    const modeTabs = document.querySelectorAll('.mode-tab');
    modeTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const mode = tab.dataset.mode;
            switchMode(mode);
        });
    });
    
    // Form submission
    countForm.addEventListener('submit', handleFormSubmit);
    
    // Error dismissal
    const dismissErrorBtn = document.getElementById('dismiss-error');
    if (dismissErrorBtn) {
        dismissErrorBtn.addEventListener('click', hideError);
    }
    
    // Results view
    filterInputs.forEach(input => {
        input.addEventListener('input', applyFiltersAndSort);
    });
    
    // Sortable headers
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.column;
            handleSort(column);
        });
    });
    
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadAllCachedResults);
    }
    
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }
    
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', exportToCSV);
    }
    
    if (exportJsonBtn) {
        exportJsonBtn.addEventListener('click', exportToJSON);
    }
    
    // Go to calc button
    const gotoCalcBtn = document.getElementById('goto-calc-btn');
    if (gotoCalcBtn) {
        gotoCalcBtn.addEventListener('click', () => switchView('calculation'));
    }
}

/**
 * Switch between input modes (single, all-n, range)
 */
function switchMode(mode) {
    // Update tab active states
    document.querySelectorAll('.mode-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`.mode-tab[data-mode="${mode}"]`).classList.add('active');
    
    // Update panel active states
    document.querySelectorAll('.input-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.getElementById(`${mode}-panel`).classList.add('active');
    
    // Update hidden radio buttons
    document.getElementById(`mode-${mode}`).checked = true;
}

/**
 * Switch between home, calculation and presentation views
 */
function switchView(viewName) {
    console.log('switchView called with:', viewName); // Debug
    
    // Remove active class from all views and buttons
    homeView.classList.remove('active');
    calculationView.classList.remove('active');
    presentationView.classList.remove('active');
    homeViewBtn.classList.remove('active');
    calcViewBtn.classList.remove('active');
    presentViewBtn.classList.remove('active');
    
    // Add active class to selected view and button
    if (viewName === 'home') {
        homeView.classList.add('active');
        homeViewBtn.classList.add('active');
        console.log('Switched to home view'); // Debug
    } else if (viewName === 'calculation') {
        calculationView.classList.add('active');
        calcViewBtn.classList.add('active');
        console.log('Switched to calculation view'); // Debug
    } else if (viewName === 'presentation') {
        presentationView.classList.add('active');
        presentViewBtn.classList.add('active');
        console.log('Switched to results view'); // Debug
        
        // Load all cached results when switching to results view
        loadAllCachedResults();
    }
}



/**
 * Handle form submission
 */
async function handleFormSubmit(event) {
    event.preventDefault();
    console.log('Form submitted!'); // Debug
    
    // Hide previous results and errors
    hideError();
    
    // Get selected mode
    const selectedMode = document.querySelector('input[name="mode"]:checked').value;
    console.log('Selected mode:', selectedMode); // Debug
    
    // Build request body based on mode
    let requestBody;
    try {
        requestBody = buildRequestBody(selectedMode);
        console.log('Request body:', requestBody); // Debug
    } catch (error) {
        console.error('Error building request:', error); // Debug
        showError(error.message);
        return;
    }
    
    // Show progress indicator with computing message
    console.log('Showing progress...'); // Debug
    showProgress('Computing results...');
    
    // First, load any cached results immediately
    console.log('Loading cached results first...'); // Debug
    try {
        await loadAndDisplayCachedResults(requestBody, selectedMode);
        console.log('Cached results loaded'); // Debug
    } catch (error) {
        console.error('Error loading cached results:', error); // Debug
    }
    
    console.log('About to make API call...'); // Debug
    
    // Start polling for progress
    const progressInterval = startProgressPolling();
    
    // Make API request
    try {
        console.log('Fetching from:', `${API_BASE_URL}/api/count`); // Debug
        const response = await fetch(`${API_BASE_URL}/api/count`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('Response received, status:', response.status); // Debug
        const data = await response.json();
        
        console.log('API Response:', data); // Debug log
        
        if (response.ok && data.status === 'success') {
            // Display results
            console.log('Displaying results:', data.results); // Debug log
            displayResults(data.results);
        } else {
            // Display error
            console.error('API Error:', data.error); // Debug log
            showError(data.error || 'An error occurred while processing your request');
            hideResults();
        }
    } catch (error) {
        console.error('Fetch error:', error); // Debug
        showError(`Network error: ${error.message}`);
        hideResults();
    } finally {
        // Stop polling
        stopProgressPolling(progressInterval);
        console.log('Hiding progress...'); // Debug
        hideProgress();
    }
}

/**
 * Build request body based on selected mode
 */
function buildRequestBody(mode) {
    if (mode === 'single') {
        const r = parseInt(document.getElementById('input-r').value);
        const n = parseInt(document.getElementById('input-n').value);
        
        if (isNaN(r) || isNaN(n)) {
            throw new Error('Please enter valid numbers for r and n');
        }
        
        if (r < 2) {
            throw new Error('r must be at least 2');
        }
        
        if (n < 2) {
            throw new Error('n must be at least 2');
        }
        
        if (r > n) {
            throw new Error('r must be less than or equal to n');
        }
        
        return { r, n };
        
    } else if (mode === 'all-n') {
        const n = parseInt(document.getElementById('input-n-only').value);
        
        if (isNaN(n)) {
            throw new Error('Please enter a valid number for n');
        }
        
        if (n < 2) {
            throw new Error('n must be at least 2');
        }
        
        return { n };
        
    } else if (mode === 'range') {
        const n_start = parseInt(document.getElementById('input-n-start').value);
        const n_end = parseInt(document.getElementById('input-n-end').value);
        
        if (isNaN(n_start) || isNaN(n_end)) {
            throw new Error('Please enter valid numbers for n start and n end');
        }
        
        if (n_start < 2) {
            throw new Error('n start must be at least 2');
        }
        
        if (n_end < 2) {
            throw new Error('n end must be at least 2');
        }
        
        if (n_start > n_end) {
            throw new Error('n start must be less than or equal to n end');
        }
        
        return { n_start, n_end };
    }
    
    throw new Error('Invalid mode selected');
}

/**
 * Start polling for progress updates
 */
function startProgressPolling() {
    console.log('Starting progress polling'); // Debug
    
    const intervalId = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/progress`);
            const data = await response.json();
            
            if (response.ok && data.status === 'success' && data.progress) {
                console.log('Progress update:', data.progress); // Debug
                // Update each progress entry in the table
                data.progress.forEach(progressData => {
                    updateProgressInTable(progressData);
                });
            }
        } catch (error) {
            console.error('Error polling progress:', error);
        }
    }, 1000); // Poll every second
    
    return intervalId;
}

/**
 * Stop polling for progress updates
 */
function stopProgressPolling(intervalId) {
    if (intervalId) {
        console.log('Stopping progress polling'); // Debug
        clearInterval(intervalId);
    }
}

/**
 * Update progress for a specific dimension in the table
 */
function updateProgressInTable(progressData) {
    const {r, n, rectangles_scanned, positive_count, negative_count, is_complete} = progressData;
    
    // Find the row for this dimension
    const rows = resultsTbody.querySelectorAll('tr');
    let targetRow = null;
    
    for (const row of rows) {
        const rCell = row.cells[0];
        const nCell = row.cells[1];
        if (rCell && nCell && parseInt(rCell.textContent) === r && parseInt(nCell.textContent) === n) {
            targetRow = row;
            break;
        }
    }
    
    if (!targetRow) {
        console.warn(`Row not found for (${r}, ${n})`);
        return;
    }
    
    // Don't update rows that already have results (cached rows)
    // Check if row has class 'result-row' which means it's already showing cached data
    if (targetRow.classList.contains('result-row')) {
        console.log(`Skipping update for cached row (${r}, ${n})`);
        return;
    }
    
    if (is_complete) {
        // Update with final values
        targetRow.className = 'result-row';
        const difference = positive_count - negative_count;
        targetRow.innerHTML = `
            <td>${r}</td>
            <td>${n}</td>
            <td>${formatNumber(positive_count)}</td>
            <td>${formatNumber(negative_count)}</td>
            <td>${formatNumber(difference)}</td>
            <td><span class="computed-badge">Computed</span></td>
        `;
    } else {
        // Update with progress
        targetRow.className = 'computing-row';
        targetRow.innerHTML = `
            <td>${r}</td>
            <td>${n}</td>
            <td colspan="4" style="text-align: center; color: var(--text-secondary);">
                <span class="computing-indicator">
                    Computing... (scanned: ${formatNumber(rectangles_scanned)}, 
                    +${formatNumber(positive_count)}, 
                    -${formatNumber(negative_count)})
                </span>
            </td>
        `;
    }
}

/**
 * Display results in the table
 */
function displayResults(results) {
    console.log('displayResults called with:', results); // Debug log
    
    // Clear previous results (including computing placeholders)
    resultsTbody.innerHTML = '';
    
    if (!results || results.length === 0) {
        console.log('No results to display'); // Debug log
        resultsTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-secondary);">No results to display</td></tr>';
        showResults();
        return;
    }
    
    console.log('Adding', results.length, 'rows to table'); // Debug log
    
    // Add each result as a table row with fade-in animation
    results.forEach((result, index) => {
        const row = document.createElement('tr');
        row.className = 'result-row';
        row.style.animationDelay = `${index * 0.05}s`;
        
        // Format numbers with commas for readability
        const positiveCount = formatNumber(result.positive_count);
        const negativeCount = formatNumber(result.negative_count);
        const difference = formatNumber(result.difference);
        
        // Determine source badge
        const sourceBadge = result.from_cache 
            ? '<span class="cached-badge">Cached</span>'
            : '<span class="computed-badge">Computed</span>';
        
        row.innerHTML = `
            <td>${result.r}</td>
            <td>${result.n}</td>
            <td>${positiveCount}</td>
            <td>${negativeCount}</td>
            <td>${difference}</td>
            <td>${sourceBadge}</td>
        `;
        
        resultsTbody.appendChild(row);
    });
    
    showResults();
}

/**
 * Format number with commas for readability
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Load and display cached results immediately, then show placeholders for uncached ones
 */
async function loadAndDisplayCachedResults(requestBody, mode) {
    // Determine what dimensions will be computed
    let dimensions = [];
    
    if (mode === 'single') {
        dimensions = [[requestBody.r, requestBody.n]];
    } else if (mode === 'all-n') {
        const n = requestBody.n;
        for (let r = 2; r <= n; r++) {
            dimensions.push([r, n]);
        }
    } else if (mode === 'range') {
        for (let n = requestBody.n_start; n <= requestBody.n_end; n++) {
            for (let r = 2; r <= n; r++) {
                dimensions.push([r, n]);
            }
        }
    }
    
    // Get the range for cache query
    const rValues = dimensions.map(d => d[0]);
    const nValues = dimensions.map(d => d[1]);
    const rMin = Math.min(...rValues);
    const rMax = Math.max(...rValues);
    const nMin = Math.min(...nValues);
    const nMax = Math.max(...nValues);
    
    // Query cache for this range
    try {
        const url = `${API_BASE_URL}/api/cache/results?r_min=${rMin}&r_max=${rMax}&n_min=${nMin}&n_max=${nMax}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (response.ok && data.status === 'success' && data.results && data.results.length > 0) {
            // Display cached results immediately
            const cachedDims = new Set(data.results.map(r => `${r.r},${r.n}`));
            
            // Clear table
            resultsTbody.innerHTML = '';
            
            // Add cached results first
            data.results.forEach(result => {
                const row = document.createElement('tr');
                row.className = 'result-row';
                
                const positiveCount = formatNumber(result.positive_count);
                const negativeCount = formatNumber(result.negative_count);
                const difference = formatNumber(result.difference);
                
                row.innerHTML = `
                    <td>${result.r}</td>
                    <td>${result.n}</td>
                    <td>${positiveCount}</td>
                    <td>${negativeCount}</td>
                    <td>${difference}</td>
                    <td><span class="cached-badge">Cached</span></td>
                `;
                
                resultsTbody.appendChild(row);
            });
            
            // Add placeholder rows for uncached dimensions
            dimensions.forEach(([r, n]) => {
                if (!cachedDims.has(`${r},${n}`)) {
                    const row = document.createElement('tr');
                    row.className = 'computing-row';
                    row.setAttribute('data-r', r);
                    row.setAttribute('data-n', n);
                    row.innerHTML = `
                        <td>${r}</td>
                        <td>${n}</td>
                        <td colspan="4" style="text-align: center; color: var(--text-secondary);">
                            <span class="computing-indicator">Computing...</span>
                        </td>
                    `;
                    resultsTbody.appendChild(row);
                }
            });
            
            showResults();
        } else {
            // No cached results, show all as computing
            showResultsWithPlaceholder(requestBody, mode);
        }
    } catch (error) {
        console.error('Error loading cached results:', error);
        // Fall back to showing all as computing
        showResultsWithPlaceholder(requestBody, mode);
    }
}

/**
 * Show results table with placeholder rows indicating what's being computed
 */
function showResultsWithPlaceholder(requestBody, mode) {
    // Clear previous results
    resultsTbody.innerHTML = '';
    
    // Determine what dimensions will be computed
    let dimensions = [];
    
    if (mode === 'single') {
        dimensions = [[requestBody.r, requestBody.n]];
    } else if (mode === 'all-n') {
        const n = requestBody.n;
        for (let r = 2; r <= n; r++) {
            dimensions.push([r, n]);
        }
    } else if (mode === 'range') {
        for (let n = requestBody.n_start; n <= requestBody.n_end; n++) {
            for (let r = 2; r <= n; r++) {
                dimensions.push([r, n]);
            }
        }
    }
    
    // Add placeholder rows
    dimensions.forEach(([r, n]) => {
        const row = document.createElement('tr');
        row.className = 'pending-row';
        row.innerHTML = `
            <td>${r}</td>
            <td>${n}</td>
            <td colspan="4" style="text-align: center; color: var(--text-secondary);">
                <span class="pending-indicator">Pending...</span>
            </td>
        `;
        resultsTbody.appendChild(row);
    });
    
    showResults();
}

/**
 * Show progress indicator
 */
function showProgress(message = 'Computing results...') {
    const progressMessage = progressIndicator.querySelector('p');
    if (progressMessage) {
        progressMessage.textContent = message;
    }
    progressIndicator.style.display = 'block';
    submitBtn.disabled = true;
}

/**
 * Hide progress indicator
 */
function hideProgress() {
    progressIndicator.style.display = 'none';
    submitBtn.disabled = false;
}

/**
 * Show error message
 */
function showError(message) {
    const errorMessage = errorDisplay.querySelector('.error-message');
    errorMessage.textContent = message;
    errorDisplay.style.display = 'block';
}

/**
 * Hide error message
 */
function hideError() {
    errorDisplay.style.display = 'none';
}

/**
 * Show results section
 */
function showResults() {
    resultsSection.style.display = 'block';
}

/**
 * Hide results section
 */
function hideResults() {
    resultsSection.style.display = 'none';
}

// ============================================================================
// Results View Functions
// ============================================================================

let allCachedResults = []; // Store all results for filtering/sorting

/**
 * Load all cached results
 */
async function loadAllCachedResults() {
    console.log('Loading all cached results...'); // Debug
    try {
        // Get all cached dimensions first
        const dimResponse = await fetch(`${API_BASE_URL}/api/cache`);
        const dimData = await dimResponse.json();
        
        if (!dimResponse.ok || dimData.status !== 'success' || !dimData.dimensions || dimData.dimensions.length === 0) {
            // No cached data
            showEmptyResults();
            return;
        }
        
        const dimensions = dimData.dimensions;
        
        // Calculate ranges
        const rValues = dimensions.map(d => d[0]);
        const nValues = dimensions.map(d => d[1]);
        const minR = Math.min(...rValues);
        const maxR = Math.max(...rValues);
        const minN = Math.min(...nValues);
        const maxN = Math.max(...nValues);
        
        // Fetch all results in range
        const url = `${API_BASE_URL}/api/cache/results?r_min=${minR}&r_max=${maxR}&n_min=${minN}&n_max=${maxN}`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (response.ok && data.status === 'success' && data.results) {
            allCachedResults = data.results;
            updateStats(allCachedResults, minR, maxR, minN, maxN);
            displayAllResults(allCachedResults);
        } else {
            showEmptyResults();
        }
    } catch (error) {
        console.error('Error loading cached results:', error);
        showEmptyResults();
    }
}

/**
 * Show empty results state
 */
function showEmptyResults() {
    emptyResultsState.style.display = 'block';
    resultsTableCard.style.display = 'none';
    document.getElementById('total-results').textContent = '0';
    document.getElementById('dimension-range').textContent = '-';
}

/**
 * Update stats cards
 */
function updateStats(results, minR, maxR, minN, maxN) {
    document.getElementById('total-results').textContent = results.length;
    document.getElementById('dimension-range').textContent = `r: ${minR}-${maxR}, n: ${minN}-${maxN}`;
}

/**
 * Display all results in table
 */
function displayAllResults(results) {
    emptyResultsState.style.display = 'none';
    resultsTableCard.style.display = 'block';
    
    if (!results || results.length === 0) {
        presentationTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">No results to display</td></tr>';
        updateFooter(0, 0);
        return;
    }
    
    // Reset sort to default (n ascending)
    currentSort = { column: 'n', direction: 'asc' };
    
    // Update sort indicator
    document.querySelectorAll('.sort-indicator').forEach(indicator => {
        indicator.className = 'sort-indicator';
    });
    document.querySelector('.sortable[data-column="n"] .sort-indicator').classList.add('asc');
    
    // Display with filters and sort applied
    applyFiltersAndSort();
}

/**
 * Handle column sort
 */
function handleSort(column) {
    // Toggle direction if same column, otherwise default to asc
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    
    // Update sort indicators
    document.querySelectorAll('.sort-indicator').forEach(indicator => {
        indicator.className = 'sort-indicator';
    });
    
    const activeHeader = document.querySelector(`.sortable[data-column="${column}"] .sort-indicator`);
    if (activeHeader) {
        activeHeader.classList.add(currentSort.direction);
    }
    
    applyFiltersAndSort();
}

/**
 * Apply filters and sorting
 */
function applyFiltersAndSort() {
    let filtered = [...allCachedResults];
    
    // Apply filters
    filterInputs.forEach(input => {
        const column = input.dataset.column;
        const value = input.value.toLowerCase().trim();
        
        if (value) {
            filtered = filtered.filter(result => {
                const cellValue = result[column === 'positive' ? 'positive_count' : 
                                         column === 'negative' ? 'negative_count' : 
                                         column].toString().toLowerCase();
                return cellValue.includes(value);
            });
        }
    });
    
    // Apply sorting
    filtered.sort((a, b) => {
        let aVal, bVal;
        
        switch(currentSort.column) {
            case 'r':
                aVal = a.r;
                bVal = b.r;
                break;
            case 'n':
                aVal = a.n;
                bVal = b.n;
                break;
            case 'positive':
                aVal = a.positive_count;
                bVal = b.positive_count;
                break;
            case 'negative':
                aVal = a.negative_count;
                bVal = b.negative_count;
                break;
            case 'difference':
                aVal = a.difference;
                bVal = b.difference;
                break;
            default:
                return 0;
        }
        
        if (currentSort.direction === 'asc') {
            return aVal - bVal;
        } else {
            return bVal - aVal;
        }
    });
    
    displayFilteredResults(filtered);
}

/**
 * Display filtered results
 */
function displayFilteredResults(results) {
    presentationTbody.innerHTML = '';
    
    if (!results || results.length === 0) {
        presentationTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-secondary);">No results match your filters</td></tr>';
        updateFooter(0, allCachedResults.length);
        return;
    }
    
    results.forEach(result => {
        const row = document.createElement('tr');
        row.dataset.r = result.r;
        row.dataset.n = result.n;
        
        const positiveCount = formatNumber(result.positive_count);
        const negativeCount = formatNumber(result.negative_count);
        const difference = formatNumber(result.difference);
        
        row.innerHTML = `
            <td><strong>${result.r}</strong></td>
            <td><strong>${result.n}</strong></td>
            <td>${positiveCount}</td>
            <td>${negativeCount}</td>
            <td>${difference}</td>
            <td class="actions-col">
                <button class="recompute-btn" onclick="recomputeResult(${result.r}, ${result.n})">
                    🔄 Recompute
                </button>
            </td>
        `;
        
        presentationTbody.appendChild(row);
    });
    
    updateFooter(results.length, allCachedResults.length);
}

/**
 * Clear all filters
 */
function clearAllFilters() {
    filterInputs.forEach(input => {
        input.value = '';
    });
    applyFiltersAndSort();
}

/**
 * Update table footer
 */
function updateFooter(showing, total) {
    document.getElementById('showing-count').textContent = showing;
    document.getElementById('total-count').textContent = total;
}

/**
 * Recompute a specific result
 */
async function recomputeResult(r, n) {
    console.log(`Recomputing (${r}, ${n})...`);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/count`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ r, n })
        });
        
        const data = await response.json();
        
        if (response.ok && data.status === 'success') {
            // Reload all results
            await loadAllCachedResults();
            alert(`Successfully recomputed (${r}, ${n})`);
        } else {
            alert(`Error recomputing: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        alert(`Network error: ${error.message}`);
    }
}

/**
 * Export results to CSV
 */
function exportToCSV() {
    if (!allCachedResults || allCachedResults.length === 0) {
        alert('No results to export');
        return;
    }
    
    // Create CSV content
    const headers = ['r', 'n', 'Positive Count', 'Negative Count', 'Difference'];
    const rows = allCachedResults.map(result => [
        result.r,
        result.n,
        result.positive_count,
        result.negative_count,
        result.difference
    ]);
    
    let csvContent = headers.join(',') + '\n';
    rows.forEach(row => {
        csvContent += row.join(',') + '\n';
    });
    
    // Download file
    downloadFile(csvContent, 'latin-rectangles.csv', 'text/csv');
}

/**
 * Export results to JSON
 */
function exportToJSON() {
    if (!allCachedResults || allCachedResults.length === 0) {
        alert('No results to export');
        return;
    }
    
    // Create JSON content
    const jsonContent = JSON.stringify(allCachedResults, null, 2);
    
    // Download file
    downloadFile(jsonContent, 'latin-rectangles.json', 'application/json');
}

/**
 * Download a file
 */
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Make recomputeResult available globally
window.recomputeResult = recomputeResult;
