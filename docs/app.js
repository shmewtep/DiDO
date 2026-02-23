import { getCQRegistry } from "./cqRegistry.js"

const engine = new Comunica.QueryEngine();
const DATA_SOURCE = 'https://raw.githubusercontent.com/shmewtep/dialogueOnt/refs/heads/edit/src/ontology/data/ami_meeting_EN2001a.ttl';
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
const bindVariables = (rawQuery, config) => {
    let bindings = "";
    config.variables.forEach(v => {
        bindings += `BIND(${v.default} AS ?${v.name}) .\n`;
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
                const resultRow = cq.output_variables.map(v => {
                    const binding = data.get(v.name);
                    console.log(`Variable ${v.name}:`, binding);
                    // Create html element
                    elements.resultsBody.innerHTML = '';
                    const th = document.createElement('th');

                    th.textContent = (binding.value).replace(prefix, 'ex:');
                    elements.resultsHead.appendChild(th);
                    return binding ? binding.value : '';
                })
                console.log(resultRow.join(' | '));
            });

        });


    } catch (err) {
        elements.resultsBody.innerHTML = `<tr><td class="placeholder" style="color: #f85149">Error: ${err.message}</td></tr>`;
    } finally {
        elements.loader.classList.add('hidden');
        elements.runBtn.disabled = false;
    }
});
