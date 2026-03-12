import { getCQRegistry } from "./cqRegistry.js"

const engine = new Comunica.QueryEngine();
const DATA_SOURCE = 'https://raw.githubusercontent.com/shmewtep/dialogueOnt/refs/heads/edit/docs/data/EN2001a_first50.ttl';
const prefix = "http://purl.org/twc/dido/individuals#";

const cqRegistry = getCQRegistry();

const store = new N3.Store();
let n3DataLoaded = false;
let n3UtterancesData = [];

const loadTTLData = async () => {
    try {
        const response = await fetch(DATA_SOURCE);
        const text = await response.text();
        const parser = new N3.Parser({ format: 'text/turtle' });
        parser.parse(text, (error, quad, prefixes) => {
            if (quad) {
                store.addQuad(quad);
            } else if (!error) {
                n3DataLoaded = true;
                processUtterances();
            } else {
                console.error("Error parsing TTL:", error);
            }
        });
    } catch (e) {
        console.error("Failed to load TTL data", e);
    }
}
loadTTLData();

function processUtterances() {
    const SIO_000068 = 'http://semanticscience.org/resource/SIO_000068';
    const SIO_000232 = 'http://semanticscience.org/resource/SIO_000232';
    const SIO_000300 = 'http://semanticscience.org/resource/SIO_000300';
    const SIO_000139 = 'http://semanticscience.org/resource/SIO_000139';
    const SIO_000008 = 'http://semanticscience.org/resource/sio_000008';
    const TIME_HAS_BEGINNING = 'http://www.w3.org/2006/time#hasBeginning';
    const TIME_HAS_END = 'http://www.w3.org/2006/time#hasEnd';
    const TIME_IN_DATETIME = 'http://www.w3.org/2006/time#inDateTime';
    const TIME_SECOND = 'http://www.w3.org/2006/time#second';

    const utterances = store.getQuads(null, SIO_000068, null).map(q => q.subject);
    
    utterances.forEach(u => {
        const id = u.value;
        const dialogue = store.getQuads(u, SIO_000068, null)[0]?.object.value;
        const textUri = store.getQuads(u, SIO_000232, null)[0]?.object;
        let text = textUri ? store.getQuads(textUri, SIO_000300, null)[0]?.object.value : "";
        if (text && text.startsWith('"') && text.endsWith('"')) {
            text = text.substring(1, text.length - 1);
        }

        const speaker = store.getQuads(u, SIO_000139, null)[0]?.object.value;
        
        const timeInfo = store.getQuads(u, SIO_000008, null)[0]?.object;
        let beginTime = 0;
        let endTime = 0;
        
        if (timeInfo) {
            const hasBeginning = store.getQuads(timeInfo, TIME_HAS_BEGINNING, null)[0]?.object;
            if (hasBeginning) {
                const inDateTime = store.getQuads(hasBeginning, TIME_IN_DATETIME, null)[0]?.object;
                if (inDateTime) {
                    const sec = store.getQuads(inDateTime, TIME_SECOND, null)[0]?.object.value;
                    beginTime = sec ? parseFloat(sec) : 0;
                }
            }
            const hasEnd = store.getQuads(timeInfo, TIME_HAS_END, null)[0]?.object;
            if (hasEnd) {
                const inDateTime = store.getQuads(hasEnd, TIME_IN_DATETIME, null)[0]?.object;
                if (inDateTime) {
                    const sec = store.getQuads(inDateTime, TIME_SECOND, null)[0]?.object.value;
                    endTime = sec ? parseFloat(sec) : 0;
                }
            }
        }
        
        n3UtterancesData.push({
            iri: id,
            id: id.replace(prefix, '').replace('utterance', ''),
            dialogue: dialogue,
            text: text,
            speaker: speaker ? speaker.replace(prefix, 'ex:').replace('ex:human', '') : "",
            beginTime: beginTime,
            endTime: endTime
        });
    });
}const elements = {
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

    if (!n3DataLoaded) {
        // Retry shortly if the page just loaded and data isn't ready
        setTimeout(() => loadConversationSnippet(dialogueIri, utteranceIri), 500);
        return;
    }

    let targetDialogue = null;
    let targetBegin = 0;

    if (utteranceIri) {
        const expandedUtteranceIri = utteranceIri.startsWith('ex:')
            ? `${prefix}${utteranceIri.replace('ex:', '')}`
            : (utteranceIri.startsWith('<') ? utteranceIri.slice(1, -1) : utteranceIri);
            
        const utterance = n3UtterancesData.find(u => u.iri === expandedUtteranceIri);
        if (utterance) {
            targetDialogue = utterance.dialogue;
            targetBegin = utterance.beginTime;
        } else {
            targetDialogue = null;
        }
    } else if (dialogueIri) {
        targetDialogue = dialogueIri.startsWith('ex:')
            ? `${prefix}${dialogueIri.replace('ex:', '')}`
            : (dialogueIri.startsWith('<') ? dialogueIri.slice(1, -1) : dialogueIri);
    }

    if (!targetDialogue) {
        elements.conversationContainer.innerHTML = '<div class="placeholder">Dialogue not found for snippet</div>';
        return;
    }

    const filtered = n3UtterancesData.filter(u => u.dialogue === targetDialogue && u.beginTime >= targetBegin);
    filtered.sort((a, b) => a.beginTime - b.beginTime);
    
    const utterances = filtered.slice(0, 15);

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
