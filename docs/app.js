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
    loader: document.getElementById('loader'),
    conversationContainer: document.getElementById('conversation-container')
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
        const val = inputValues[name];
        // If it starts with 'ex:', expand to full IRI for binding, else wrap correctly
        if (val.startsWith('ex:')) {
            bindings += `BIND(<${prefix}${val.replace('ex:', '')}> AS ?${name}) .\n`;
        } else if (val.startsWith('<') && val.endsWith('>')) {
            bindings += `BIND(${val} AS ?${name}) .\n`;
        } else {
            bindings += `BIND("${val}" AS ?${name}) .\n`;
        }
    });
    // Inject BINDs into WHERE clause
    return rawQuery.replace('WHERE {', `WHERE {\n  ${bindings}`);
}

// Conversation snippet loader
const loadConversationSnippet = async (dialogueIri, utteranceIri = null) => {
    elements.conversationContainer.innerHTML = '<div class="loader"></div>';

    let snippetQuery = "";

    if (utteranceIri) {
        // If we have an utterance, we need to find its dialogue and then query utterances
        // We'll get utterances that happen during or after the target utterance's start time
        const expandedUtteranceIri = utteranceIri.startsWith('ex:')
            ? `<${prefix}${utteranceIri.replace('ex:', '')}>`
            : (utteranceIri.startsWith('<') ? utteranceIri : `<${utteranceIri}>`);

        snippetQuery = `
        PREFIX dido: <http://purl.org/twc/dido#>
        PREFIX sio: <http://semanticscience.org/resource/>
        PREFIX time: <http://www.w3.org/2006/time#>
        SELECT ?utterance ?text ?speaker ?beginTime ?endTime WHERE {
            # Find the target utterance's begin time and dialogue
            ${expandedUtteranceIri} sio:SIO_000068 ?dialogue ;
                                    sio:sio_000008 [ time:hasBeginning [ time:inDateTime [ time:second ?targetBegin ] ] ] .
            
            # Now find utterances in the same dialogue
            ?utterance sio:SIO_000068 ?dialogue ;
                       sio:SIO_000232 ?textUri ;
                       sio:SIO_000139 ?speaker ;
                       sio:sio_000008 [ 
                           time:hasBeginning [ time:inDateTime [ time:second ?beginTime ] ] ;
                           time:hasEnd [ time:inDateTime [ time:second ?endTime ] ]
                       ] .
            ?textUri sio:SIO_000300 ?text .
            
            # Only include utterances starting during or after the target utterance
            FILTER(?beginTime >= ?targetBegin)
        } ORDER BY ?beginTime LIMIT 15
        `;
    } else {
        // Fallback to querying just by dialogue IRI
        const expandedIri = dialogueIri.startsWith('ex:')
            ? `<${prefix}${dialogueIri.replace('ex:', '')}>`
            : (dialogueIri.startsWith('<') ? dialogueIri : `<${dialogueIri}>`);

        snippetQuery = `
        PREFIX dido: <http://purl.org/twc/dido#>
        PREFIX sio: <http://semanticscience.org/resource/>
        PREFIX time: <http://www.w3.org/2006/time#>
        SELECT ?utterance ?text ?speaker ?beginTime ?endTime WHERE {
            ?utterance sio:SIO_000068 ${expandedIri} ;
                       sio:SIO_000232 ?textUri ;
                       sio:SIO_000139 ?speaker ;
                       sio:sio_000008 [ 
                           time:hasBeginning [ time:inDateTime [ time:second ?beginTime ] ] ;
                           time:hasEnd [ time:inDateTime [ time:second ?endTime ] ]
                       ] .
            ?textUri sio:SIO_000300 ?text .
        } ORDER BY ?beginTime LIMIT 15
        `;
    }

    try {
        const bindingsStream = await new Comunica.QueryEngine().queryBindings(snippetQuery, {
            sources: [DATA_SOURCE],
        });

        const utterances = [];
        bindingsStream.on('data', (binding) => {
            utterances.push({
                id: binding.get('utterance').value.replace(prefix, '').replace('utterance', ''),
                text: binding.get('text').value,
                speaker: binding.get('speaker').value.replace(prefix, 'ex:').replace('ex:human', ''),
                beginTime: binding.get('beginTime').value,
                endTime: binding.get('endTime').value
            });
        });

        bindingsStream.on('end', () => {
            if (utterances.length === 0) {
                elements.conversationContainer.innerHTML = '<div class="placeholder">No dialogue snippet found</div>';
                return;
            }

            elements.conversationContainer.innerHTML = '';

            // Assign right side to first speaker, left to others
            const speakers = [...new Set(utterances.map(u => u.speaker))];
            const mySpeaker = speakers[0];

            utterances.forEach((u, index) => {
                const isMine = u.speaker === mySpeaker;
                const alignment = isMine ? 'right' : 'left';

                // Format time assuming seconds
                const startSecs = Math.floor(parseFloat(u.beginTime));
                const endSecs = Math.floor(parseFloat(u.endTime));

                const startMins = String(Math.floor(startSecs / 60)).padStart(2, '0');
                const startRemainder = String(startSecs % 60).padStart(2, '0');

                const endMins = String(Math.floor(endSecs / 60)).padStart(2, '0');
                const endRemainder = String(endSecs % 60).padStart(2, '0');

                const timeString = `${startMins}:${startRemainder} - ${endMins}:${endRemainder}`;

                const el = document.createElement('div');
                el.className = `message-box ${alignment}`;

                // Highlight the first utterance if we queried based on a specific utterance
                const highlightStyle = (utteranceIri && index === 0) ? `style="border: 2px solid var(--accent-primary); box-shadow: 0 0 10px rgba(88, 166, 255, 0.5);"` : '';

                el.innerHTML = `
                    <div class="message-meta">
                        <span class="message-speaker">${u.speaker}</span>
                        <span class="message-time">${timeString}</span>
                    </div>
                    <div class="message-bubble" ${highlightStyle}>
                        ${u.text}
                        <div style="font-size: 0.65rem; color: rgba(255,255,255,0.4); text-align: right; margin-top: 4px;">#${u.id}</div>
                    </div>
                `;
                elements.conversationContainer.appendChild(el);
            });
        });

        bindingsStream.on('error', (err) => {
            elements.conversationContainer.innerHTML = `<div class="placeholder" style="color: #f85149">Error loading snippet: ${err.message}</div>`;
        });
    } catch (err) {
        elements.conversationContainer.innerHTML = `<div class="placeholder" style="color: #f85149">Error loading snippet: ${err.message}</div>`;
    }
};

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

    // Load the conversation snippet based on 'utterance', 'utterance1', or 'dialogue'
    const targetUtterance = inputValues['utterance'] || inputValues['utterance1'];

    if (targetUtterance && targetUtterance.trim() !== '') {
        loadConversationSnippet(null, targetUtterance);
    } else if (inputValues['dialogue'] && inputValues['dialogue'].trim() !== '') {
        loadConversationSnippet(inputValues['dialogue'], null);
    } else {
        elements.conversationContainer.innerHTML = '<div class="placeholder">Select a question with an utterance or dialogue input and run to load examples</div>';
    }

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
