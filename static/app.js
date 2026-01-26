// API base URL
const API_BASE = '/api';

// State
let currentSchema = null;
let queryHistory = [];
let availableDatabases = [];
let currentDatabase = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await checkHealth();
    await loadDatabases();
    await loadSchema();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    const queryInput = document.getElementById('queryInput');

    // Allow Ctrl+Enter to submit
    queryInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            generateQuery();
        }
    });
}

// Check API health
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/../health`);
        const data = await response.json();

        if (data.status === 'healthy') {
            updateStatus('Connected', true);
        } else {
            updateStatus('Disconnected', false);
        }
    } catch (error) {
        console.error('Health check failed:', error);
        updateStatus('Connection Error', false);
    }
}

// Update connection status
function updateStatus(text, isHealthy) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    statusText.textContent = text;
    statusDot.style.background = isHealthy ? 'var(--success)' : 'var(--danger)';
}

// Load database schema
async function loadSchema() {
    const schemaBrowser = document.getElementById('schemaBrowser');

    try {
        const response = await fetch(`${API_BASE}/schema`);
        currentSchema = await response.json();

        renderSchema(currentSchema);
    } catch (error) {
        console.error('Failed to load schema:', error);
        schemaBrowser.innerHTML = `
            <div class="error-message">
                Failed to load schema: ${error.message}
            </div>
        `;
    }
}

// Load list of databases
async function loadDatabases() {
    try {
        const response = await fetch(`${API_BASE}/databases`);
        const data = await response.json();

        availableDatabases = data.databases || [];
        currentDatabase = data.current;

        renderDatabaseSelector();
    } catch (error) {
        console.error('Failed to load databases:', error);
    }
}

// Render database selector
function renderDatabaseSelector() {
    const schemaBrowser = document.getElementById('schemaBrowser');

    if (availableDatabases.length === 0) {
        return;
    }

    const selectorHTML = `
        <div style="margin-bottom: 1rem; padding: 0.75rem; background: var(--bg-secondary); border-radius: 8px;">
            <label style="display: block; margin-bottom: 0.5rem; font-size: 0.875rem; color: var(--text-secondary);">
                Database:
            </label>
            <select id="databaseSelector" onchange="switchDatabase(this.value)"
                    style="width: 100%; padding: 0.5rem; background: var(--bg-primary); color: var(--text-primary); border: 1px solid var(--border-color); border-radius: 6px; cursor: pointer;">
                ${availableDatabases.map(db => `
                    <option value="${escapeHtml(db)}" ${db === currentDatabase ? 'selected' : ''}>
                        ${db === currentDatabase ? '● ' : ''}${escapeHtml(db)}
                    </option>
                `).join('')}
            </select>
            <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-muted);">
                ${availableDatabases.length} databases available
            </div>
        </div>
        <div id="schemaContent"></div>
    `;

    schemaBrowser.innerHTML = selectorHTML;
}

// Switch to a different database
async function switchDatabase(database) {
    const schemaBrowser = document.getElementById('schemaBrowser');
    const selector = document.getElementById('databaseSelector');

    // Show loading
    if (selector) {
        selector.disabled = true;
    }

    const schemaContent = document.getElementById('schemaContent');
    if (schemaContent) {
        schemaContent.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
                <span>Switching to ${escapeHtml(database)}...</span>
            </div>
        `;
    }

    try {
        const response = await fetch(`${API_BASE}/switch-database?database=${encodeURIComponent(database)}`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            currentDatabase = database;

            // Reload schema
            await loadSchema();

            // Re-render database selector with updated schema
            renderDatabaseSelector();

            // Show success notification
            showNotification(`Switched to database: ${database} (${result.tables_count} tables)`, 'success');
        } else {
            throw new Error(`Failed to switch database: ${response.statusText}`);
        }
    } catch (error) {
        console.error('Error switching database:', error);
        showNotification(`Failed to switch to ${database}: ${error.message}`, 'error');

        // Restore previous selection
        if (selector) {
            selector.value = currentDatabase;
        }
    } finally {
        if (selector) {
            selector.disabled = false;
        }
    }
}

// Render schema in sidebar
function renderSchema(schema) {
    let schemaBrowser = document.getElementById('schemaContent');

    // Fallback to schemaBrowser if schemaContent doesn't exist yet
    if (!schemaBrowser) {
        schemaBrowser = document.getElementById('schemaBrowser');
    }

    if (!schema || !schema.tables || schema.tables.length === 0) {
        schemaBrowser.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <p>No tables found in this database</p>
            </div>
        `;
        return;
    }

    const tablesHTML = schema.tables.map(table => `
        <div class="table-item" onclick="toggleTable(this)">
            <div class="table-name">${table.name}</div>
            <div class="column-list">
                ${table.columns.map(col => `
                    <div class="column-item">
                        ${col.is_primary_key ? '🔑 ' : ''}${col.name}
                        <span class="column-type">${col.type}</span>
                        ${col.nullable ? '' : ' NOT NULL'}
                    </div>
                `).join('')}
                ${table.foreign_keys && table.foreign_keys.length > 0 ? `
                    <div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border-color);">
                        ${table.foreign_keys.map(fk => `
                            <div class="column-item">
                                🔗 ${fk.column} → ${fk.references_table}.${fk.references_column}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');

    schemaBrowser.innerHTML = tablesHTML;
}

// Toggle table expansion
function toggleTable(element) {
    element.classList.toggle('expanded');
}

// Generate SQL query
async function generateQuery() {
    const queryInput = document.getElementById('queryInput');
    const generateBtn = document.getElementById('generateBtn');
    const outputContainer = document.getElementById('outputContainer');

    const userRequest = queryInput.value.trim();

    if (!userRequest) {
        showError('Please enter a query request');
        return;
    }

    // Disable button and show loading
    generateBtn.disabled = true;
    outputContainer.innerHTML = `
        <div class="card">
            <div class="loading">
                <div class="spinner"></div>
                <span>Generating query...</span>
            </div>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/generate-query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                request: userRequest,
                conversation_history: null
            })
        });

        const result = await response.json();

        if (result.error) {
            showError(result.error);
        } else {
            displayQueryResult(result, userRequest);
            addToHistory(userRequest, result.query_type);
        }
    } catch (error) {
        console.error('Failed to generate query:', error);
        showError(`Failed to generate query: ${error.message}`);
    } finally {
        generateBtn.disabled = false;
    }
}

// Display query result
function displayQueryResult(result, userRequest) {
    const outputContainer = document.getElementById('outputContainer');

    const typeClass = `type-${result.query_type.toLowerCase()}`;
    const safetyClass = result.is_safe ? 'safe' : 'unsafe';

    outputContainer.innerHTML = `
        <div class="card query-output">
            <div class="query-meta">
                <span class="meta-badge ${typeClass}">
                    ${getTypeIcon(result.query_type)} ${result.query_type}
                </span>
                <span class="meta-badge ${safetyClass}">
                    ${result.is_safe ? '✅ Safe' : '⚠️ Review Required'}
                </span>
                ${result.tables_used.length > 0 ? `
                    <span class="meta-badge">
                        📊 Tables: ${result.tables_used.join(', ')}
                    </span>
                ` : ''}
            </div>
            
            ${result.warnings ? `
                <div class="warning-box">
                    <strong>⚠️ Warning:</strong> ${result.warnings}
                </div>
            ` : ''}
            
            <div class="explanation">
                <strong>Explanation:</strong> ${result.explanation}
            </div>
            
            <div class="sql-container">
                <button class="copy-btn" onclick="copyToClipboard(this)">
                    📋 Copy
                </button>
                <pre class="sql-code">${escapeHtml(result.query || 'No query generated')}</pre>
            </div>
            
            ${!result.is_safe ? `
                <div class="warning-box">
                    <strong>⚠️ Important:</strong> This query has not been executed. 
                    Please review it carefully before running it on your database.
                </div>
            ` : `
                <div style="color: var(--text-muted); font-size: 0.875rem; margin-top: 1rem;">
                    💡 <strong>Note:</strong> This query has not been executed. 
                    Copy and review it before running on your database.
                </div>
            `}
        </div>
    `;
}

// Get icon for query type
function getTypeIcon(type) {
    const icons = {
        'SELECT': '🔍',
        'INSERT': '➕',
        'UPDATE': '✏️',
        'DELETE': '🗑️'
    };
    return icons[type] || '📝';
}

// Show error message
function showError(message) {
    const outputContainer = document.getElementById('outputContainer');
    outputContainer.innerHTML = `
        <div class="card">
            <div class="error-message">
                <strong>Error:</strong> ${escapeHtml(message)}
            </div>
        </div>
    `;
}

// Copy to clipboard
async function copyToClipboard(button) {
    const sqlCode = button.parentElement.querySelector('.sql-code').textContent;

    try {
        await navigator.clipboard.writeText(sqlCode);
        button.textContent = '✅ Copied!';
        setTimeout(() => {
            button.textContent = '📋 Copy';
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
        button.textContent = '❌ Failed';
        setTimeout(() => {
            button.textContent = '📋 Copy';
        }, 2000);
    }
}

// Add to query history
function addToHistory(request, queryType) {
    queryHistory.unshift({
        request,
        queryType,
        timestamp: new Date().toISOString()
    });

    // Keep only last 10
    if (queryHistory.length > 10) {
        queryHistory = queryHistory.slice(0, 10);
    }

    renderHistory();
}

// Render query history
function renderHistory() {
    const historyList = document.getElementById('historyList');

    if (queryHistory.length === 0) {
        historyList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <p>No queries yet</p>
            </div>
        `;
        return;
    }

    historyList.innerHTML = queryHistory.map(item => `
        <div class="history-item" onclick="loadFromHistory('${escapeHtml(item.request)}')">
            <div class="history-request">${escapeHtml(item.request)}</div>
            <div class="history-type">${getTypeIcon(item.queryType)} ${item.queryType}</div>
        </div>
    `).join('');
}

// Load query from history
function loadFromHistory(request) {
    document.getElementById('queryInput').value = request;
    document.getElementById('queryInput').focus();
}

// Clear output
function clearOutput() {
    document.getElementById('queryInput').value = '';
    document.getElementById('outputContainer').innerHTML = '';
}

// Refresh schema
async function refreshSchema() {
    const refreshBtn = document.getElementById('refreshSchemaBtn');
    refreshBtn.disabled = true;

    try {
        await fetch(`${API_BASE}/refresh-schema`, { method: 'POST' });
        await loadSchema();
        showNotification('Schema refreshed successfully', 'success');
    } catch (error) {
        console.error('Failed to refresh schema:', error);
        showNotification('Failed to refresh schema', 'error');
    } finally {
        refreshBtn.disabled = false;
    }
}

// Show notification
function showNotification(message, type) {
    // Simple console notification for now
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
