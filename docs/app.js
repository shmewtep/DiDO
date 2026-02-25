import { getCQRegistry } from "./cqRegistry.js"

const engine = new Comunica.QueryEngine();
const DATA_SOURCE = 'https://raw.githubusercontent.com/shmewtep/dialogueOnt/refs/heads/edit/src/ontology/data/dialog_ami/ami_meeting_EN2001a.ttl';
const prefix = "http://purl.org/twc/dido/individuals#";

const cqRegistry = getCQRegistry();

const elements = {
    cqSelect: document.getElementById('cq-select'),
    varInputs: document.getElementById('variable-inputs'),
    runBtn: document.getElementById('run-btn'),
    queryDisplay: document.getElementById('query-display'),
    toggleQuery: document.getElementById('toggle-query'),
    resultsHead: document.getElementById('table-head'),
    resultsBody: document.getElementById('table-body'),
    loader: document.getElementById('loader')
};

// Initialize CQ Registry; populate query dropdown menu
const initCQSelect = () => {
    Object.entries(cqRegistry).forEach(([id, cq]) => {
        const option = document.createElement('option');
        option.value = id;
        option.textContent = `${id}: ${cq.text}`;
        elements.cqSelect.appendChild(option);
    });

    // If a query is selected (e.g. by default or browser cache), load it
    if (elements.cqSelect.value) {
        loadCQ(elements.cqSelect.value);
    } else {
        // Otherwise, select and load the first query by default
        const firstId = Object.keys(cqRegistry)[0];
        if (firstId) {
            elements.cqSelect.value = firstId;
            loadCQ(firstId);
        }
    }
};

let currentQueryTemplate = '';

const loadCQ = async (cqId) => {
    const cq = cqRegistry[cqId];
    if (!cq) return;

    elements.runBtn.disabled = true;
    elements.varInputs.innerHTML = '';

    try {
        const response = await fetch(cq.file);
        currentQueryTemplate = await response.text();
        elements.queryDisplay.innerHTML = `<code>${currentQueryTemplate.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code>`;

        // Generate inputs
        cq.variables.forEach(v => {
            const div = document.createElement('div');
            div.className = 'field';
            div.innerHTML = `
                <label>${v.label}</label>
                <input type="text" data-var="${v.name}" value="${v.default}" placeholder="${v.placeholder}">
            `;
            elements.varInputs.appendChild(div);
        });

        elements.runBtn.disabled = false;
    } catch (err) {
        console.error('Error loading query:', err);
    }
};


initCQSelect();

// Add event listener to query dropdown menu
elements.cqSelect.addEventListener('change', (e) => loadCQ(e.target.value));

elements.toggleQuery.addEventListener('click', () => {
    elements.queryDisplay.classList.toggle('hidden');
});


// According to the query registry, load the query template and variables and BIND to specific values
const bindVariables = (rawQuery, inputValues) => {
    let bindings = "";
    Object.keys(inputValues).forEach(name => {
        bindings += `BIND(${inputValues[name]} AS ?${name}) .\n`;
    });
    // Inject BINDs into WHERE clause
    return rawQuery.replace('WHERE {', `WHERE {\n  ${bindings}`);
}

// Add event listener to run button

elements.runBtn.addEventListener('click', async () => {
    const cqId = elements.cqSelect.value;
    const cq = cqRegistry[cqId];
    if (!cq) return;
    console.log(cq);

    let rawQuery = currentQueryTemplate;

    const inputValues = {};
    if (cq.variables) {
        cq.variables.forEach(v => {
            const input = elements.varInputs.querySelector(`input[data-var="${v.name}"]`);
            inputValues[v.name] = input && input.value.trim() !== '' ? input.value.trim() : v.default;
        });
    }

    let query = bindVariables(rawQuery, inputValues);

    elements.runBtn.disabled = true;
    elements.loader.classList.remove('hidden');
    elements.resultsBody.innerHTML = '<tr><td class="placeholder">Running query...</td></tr>';
    elements.resultsHead.innerHTML = '';

    // Try to run the query
    try {
        console.log(query);
        new Comunica.QueryEngine().queryBindings(query, {
            sources: [DATA_SOURCE],
        }).then(function (bindingsStream) {
            let hasResults = false;
            let headersCreated = false;
            elements.resultsBody.innerHTML = '';

            bindingsStream.on('data', function (data) {
                // Tracking if we have received at least one row
                hasResults = true;

                // Construct the table header row if it hasn't been generated yet
                if (!headersCreated) {
                    cq.output_variables.forEach(v => {
                        const th = document.createElement('th');
                        th.textContent = v.label || v.name;
                        elements.resultsHead.appendChild(th);
                    });
                    headersCreated = true;
                }

                // Create a row corresponding to this specific binding matching the output
                const tr = document.createElement('tr');
                cq.output_variables.forEach(v => {
                    const td = document.createElement('td');
                    const binding = data.get(v.name);
                    // Extract value and clean up prefixes to be ex: if applicable
                    td.textContent = binding ? binding.value.replace(prefix, 'ex:') : '';
                    tr.appendChild(td);
                });
                elements.resultsBody.appendChild(tr);
            });

            // Fired when the query succeeds, but there are no more records to return 
            bindingsStream.on('end', function () {
                // If the query returned zero records, notify the user with an empty-state
                if (!hasResults) {
                    elements.resultsBody.innerHTML = `<tr><td colspan="${cq.output_variables.length}" class="placeholder">No results found</td></tr>`;
                    // Generate the header matching our output definition even if empty
                    cq.output_variables.forEach(v => {
                        const th = document.createElement('th');
                        th.textContent = v.label || v.name;
                        elements.resultsHead.appendChild(th);
                    });
                }
                // Hide the loader and re-enable the run button when execution completes
                elements.loader.classList.add('hidden');
                elements.runBtn.disabled = false;
            });

            // Fired for upstream errors with the stream endpoint during stream ingestion
            bindingsStream.on('error', function (err) {
                elements.resultsBody.innerHTML = `<tr><td colspan="${cq.output_variables.length}" class="placeholder" style="color: #f85149">Error: ${err.message}</td></tr>`;
                elements.loader.classList.add('hidden');
                elements.runBtn.disabled = false;
            });

        }).catch(function (err) {
            elements.resultsBody.innerHTML = `<tr><td colspan="${cq.output_variables.length}" class="placeholder" style="color: #f85149">Error: ${err.message}</td></tr>`;
            elements.loader.classList.add('hidden');
            elements.runBtn.disabled = false;
        });

    } catch (err) {
        elements.resultsBody.innerHTML = `<tr><td class="placeholder" style="color: #f85149">Error: ${err.message}</td></tr>`;
        elements.loader.classList.add('hidden');
        elements.runBtn.disabled = false;
    }
});
