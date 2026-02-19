const cqRegistry = {
    CQ1: {
        file: 'queries/CQ1.sparql',
        text: 'How many participants are involved in this dialogue?',
        variables: [{
            name: 'dialogue',
            label: 'Dialogue IRI',
            placeholder: '<http://purl.org/twc/dido/individuals#dialogue/300>',
            default: '<http://purl.org/twc/dido/individuals#dialogue/300>'
        }]
    },
    CQ2: {
        file: 'queries/CQ2.sparql',
        text: 'Which participant is associated with this utterance?',
        variables: [{
            name: 'utterance',
            label: 'Utterance IRI',
            placeholder: 'utterances:utterance_300_86',
            default: 'utterances:utterance_300_86'
        }]
    },
    CQ3: {
        file: 'queries/CQ3.sparql',
        text: 'Which utterance directly follows this utterance?',
        variables: [{
            name: 'utterance',
            label: 'Utterance IRI',
            placeholder: 'utterances:utterance_300_86',
            default: 'utterances:utterance_300_86'
        }]
    }, // Placeholder needs BIND in CQ3
    CQ4: {
        file: 'queries/CQ4.sparql',
        text: 'Which utterances occur between these two times?',
        variables: [
            { name: 'T1', label: 'Start Time (s)', placeholder: '36.5', default: '36.5' },
            { name: 'T2', label: 'End Time (s)', placeholder: '50.0', default: '50.0' }
        ]
    },
    CQ5: {
        file: 'queries/CQ5.sparql',
        text: 'Which utterances overlap with this utterance?',
        variables: [{
            name: 'utterance',
            label: 'Utterance IRI',
            placeholder: 'utterances:utterance_300_86',
            default: 'utterances:utterance_300_86'
        }]
    },
    CQ6: {
        file: 'queries/CQ6.sparql',
        text: 'How many times do the utterances of speaker S1 overlap with the utterances of speaker S2?',
        variables: [
            { name: 'S1', label: 'Speaker 1 IRI', placeholder: '<http://purl.org/twc/dido/individuals#interlocutors/ellie>', default: '<http://purl.org/twc/dido/individuals#interlocutors/ellie>' },
            { name: 'S2', label: 'Speaker 2 IRI', placeholder: '<http://purl.org/twc/dido/individuals#interlocutors/interlocutor_300>', default: '<http://purl.org/twc/dido/individuals#interlocutors/interlocutor_300>' }
        ]
    }
};



export function getCQRegistry() {
    return cqRegistry;
}
