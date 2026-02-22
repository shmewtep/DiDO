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

// Add event listener to run button
elements.runBtn.addEventListener('click', async () => {
    const cqId = elements.cqSelect.value;
    const cq = cqRegistry[cqId];
    if (!cq) return;
    console.log(cq);

    let query = currentQueryTemplate;
    console.log(query);

    // Simple substitution based on CQ patterns
    if (cqId === 'CQ4') {
        const t1 = document.querySelector('[data-var="T1"]').value;
        const t2 = document.querySelector('[data-var="T2"]').value;
        query = query.replace('36.5', t1).replace('50.0', t2);
    } else if (cqId === 'CQ2') {
        const utt = document.querySelector('[data-var="utterance"]').value;
        query = query.replace('utterances:utterance_300_86', utt);
    } else if (cqId === 'CQ3' || cqId === 'CQ5') {
        const utt = document.querySelector('[data-var="utterance"]').value;
        // If query doesn't have a BIND for ?u yet, we might need a more generic way.
        // For CQ3/CQ5 in the repo, they are generic. We'll ADD a BIND if needed or replace placeholders.
        if (query.includes('?u')) {
            query = query.replace('WHERE {', `WHERE {\n  BIND(${utt} AS ?u)`);
        }
    } else if (cqId === 'CQ6') {
        const s1 = document.querySelector('[data-var="S1"]').value;
        const s2 = document.querySelector('[data-var="S2"]').value;
        query = query + `\n  # Injected filter for demo\n  FILTER (?s1 = ${s1} && ?s2 = ${s2})`;
    }

    elements.runBtn.disabled = true;
    elements.loader.classList.remove('hidden');
    elements.resultsBody.innerHTML = '<tr><td class="placeholder">Running query...</td></tr>';
    elements.resultsHead.innerHTML = '';

    // Try to run the query
    try {

        new Comunica.QueryEngine().queryBindings(query, {
            sources: [DATA_SOURCE],
        }).then(function (bindingsStream) {
            bindingsStream.on('data', function (data) {
                // Each variable binding is an RDFJS term
                console.log(data.get('dialogue').value + ' ' + data.get('participantCount').value);
            });
        });

        const result = await engine.queryBindings(query, {
            sources: [DATA_SOURCE],
        });

        const bindings = await result.toArray();
        elements.resultsBody.innerHTML = '';

        console.log(bindings[0]);

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
