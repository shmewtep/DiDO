const engine = new window.Comunica.QuerySparql();
const DATA_SOURCE = 'data/daicwoz_dialogue_300.ttl';

const cqRegistry = {
    CQ1: { file: 'queries/CQ1.sparql', variables: [{ name: 'dialogue', label: 'Dialogue IRI', placeholder: '<http://purl.org/twc/dido/individuals#dialogue/300>', default: '<http://purl.org/twc/dido/individuals#dialogue/300>' }] },
    CQ2: { file: 'queries/CQ2.sparql', variables: [{ name: 'utterance', label: 'Utterance IRI', placeholder: 'utterances:utterance_300_86', default: 'utterances:utterance_300_86' }] },
    CQ3: { file: 'queries/CQ3.sparql', variables: [{ name: 'utterance', label: 'Utterance IRI', placeholder: 'utterances:utterance_300_86', default: 'utterances:utterance_300_86' }] }, // Placeholder needs BIND in CQ3
    CQ4: {
        file: 'queries/CQ4.sparql', variables: [
            { name: 'T1', label: 'Start Time (s)', placeholder: '36.5', default: '36.5' },
            { name: 'T2', label: 'End Time (s)', placeholder: '50.0', default: '50.0' }
        ]
    },
    CQ5: { file: 'queries/CQ5.sparql', variables: [{ name: 'utterance', label: 'Utterance IRI', placeholder: 'utterances:utterance_300_86', default: 'utterances:utterance_300_86' }] },
    CQ6: {
        file: 'queries/CQ6.sparql', variables: [
            { name: 'S1', label: 'Speaker 1 IRI', placeholder: '<http://purl.org/twc/dido/individuals#interlocutors/ellie>', default: '<http://purl.org/twc/dido/individuals#interlocutors/ellie>' },
            { name: 'S2', label: 'Speaker 2 IRI', placeholder: '<http://purl.org/twc/dido/individuals#interlocutors/interlocutor_300>', default: '<http://purl.org/twc/dido/individuals#interlocutors/interlocutor_300>' }
        ]
    }
};

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

let currentQueryTemplate = '';

elements.cqSelect.addEventListener('change', async (e) => {
    const cqId = e.target.value;
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
});

elements.toggleQuery.addEventListener('click', () => {
    elements.queryDisplay.classList.toggle('hidden');
});

elements.runBtn.addEventListener('click', async () => {
    const cqId = elements.cqSelect.value;
    const cq = cqRegistry[cqId];
    if (!cq) return;

    let query = currentQueryTemplate;

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

    try {
        const result = await engine.queryBindings(query, {
            sources: [{ type: 'file', value: DATA_SOURCE }],
        });

        const bindings = await result.toArray();
        elements.resultsBody.innerHTML = '';

        if (bindings.length === 0) {
            elements.resultsBody.innerHTML = '<tr><td class="placeholder">No results found</td></tr>';
        } else {
            const vars = Object.keys(bindings[0].toObject());
            vars.forEach(v => {
                const th = document.createElement('th');
                th.textContent = v;
                elements.resultsHead.appendChild(th);
            });

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
