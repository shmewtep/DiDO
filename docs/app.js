import { getCQRegistry } from "./cqRegistry.js"

const engine = new Comunica.QueryEngine();
const DATA_SOURCE = 'https://raw.githubusercontent.com/shmewtep/dialogueOnt/refs/heads/edit/src/ontology/data/ami_meeting_EN2001a.ttl';

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
const bindVariables = (rawQuery, config) => {
    let bindings = "";
    config.variables.forEach(v => {
        bindings += `BIND(${v.default} AS ?${v.name}).\n`;
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

    let query = bindVariables(rawQuery, cq);

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
            console.log(cq.variables);
            bindingsStream.on('data', function (data) {
                console.log('data');
                console.log(data);
                const resultRow = cq.variables.map(v => {
                    const binding = data.get(v.name);
                    return binding ? binding.value : '';
                })
                console.log(resultRow.join(' | '));
            });

        });

        const result = await engine.queryBindings(query, {
            sources: [DATA_SOURCE],
        });

        const bindings = await result.toArray();
        elements.resultsBody.innerHTML = '';

        // Handle variables from result stream metadata
        const vars = result.variables.map(v => v.value);
        vars.forEach(v => {
            const th = document.createElement('th');
            th.textContent = v;
            elements.resultsHead.appendChild(th);
        });

        if (bindings.length === 0) {
            elements.resultsBody.innerHTML = '<tr><td class="placeholder">No results found</td></tr>';
        } else {
            bindings.forEach(binding => {
                const tr = document.createElement('tr');
                vars.forEach(v => {
                    const td = document.createElement('td');
                    const value = binding.get(v);
                    td.textContent = value ? value.value : '';
                    tr.appendChild(td);
                });
                elements.resultsBody.appendChild(tr);
            });
        }
    } catch (err) {
        elements.resultsBody.innerHTML = `<tr><td class="placeholder" style="color: #f85149">Error: ${err.message}</td></tr>`;
    } finally {
        elements.loader.classList.add('hidden');
        elements.runBtn.disabled = false;
    }
});
