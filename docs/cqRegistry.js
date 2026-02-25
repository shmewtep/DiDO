const cqRegistry = {
    CQ1: {
        file: 'queries/CQ1.sparql',
        text: 'How many participants are involved in this dialogue?',
        variables: [{
            name: 'dialogue',
            label: 'Dialogue IRI',
            default: 'ex:dialogueEN2001a'
        }],
        output_variables: [{
            name: 'dialogue',
            label: 'Dialogue IRI',
        },
        {
            name: 'participantCount',
            label: 'Number of Participants',
        }]
    },
    CQ2: {
        file: 'queries/CQ2.sparql',
        text: 'Which participant is associated with this utterance?',
        variables: [{
            name: 'utterance',
            label: 'Utterance IRI',
            default: 'ex:utteranceEN2001a0'
        }],
        output_variables: [
            {
                name: 'utterance',
                label: 'Utterance IRI'
            },
            {
                name: 'participant',
                label: 'Participant IRI',
            }]
    },
    CQ3: {
        file: 'queries/CQ3.sparql',
        text: 'Which utterance directly follows this utterance?',
        variables: [{
            name: 'utterance',
            label: 'Utterance IRI',
            default: 'ex:utteranceEN2001a0'
        }],
        output_variables: [{
            name: 'utterance',
            label: 'Utterance IRI'
        },
        {
            name: 'successor',
            label: 'Next Utterance IRI'
        }]
    },
    CQ4: {
        file: 'queries/CQ4.sparql',
        text: 'Which utterances occur between these two times?',
        variables: [
            { name: 'T1', label: 'Start Time (s)', default: '0.0' },
            { name: 'T2', label: 'End Time (s)', default: '15.0' }
        ],
        output_variables: [{
            name: 'utterance',
            label: 'Utterance IRI'
        }]
    },
    CQ5: {
        file: 'queries/CQ5.sparql',
        text: 'Which utterances overlap with this utterance?',
        variables: [{
            name: 'utterance1',
            label: 'Utterance IRI',
            default: 'ex:utteranceEN2001a793'
        }],
        output_variables: [{
            name: 'utterance1',
            label: 'Utterance IRI'
        },
        {
            name: 'utterance2',
            label: 'Overlapping Utterance IRI'
        }]
    },
    CQ6: {
        file: 'queries/CQ6.sparql',
        text: 'How many times do the utterances of speaker S1 overlap with the utterances of speaker S2?',
        variables: [
            { name: 'S1', label: 'Speaker 1 IRI', default: 'ex:humanFEE065' },
            { name: 'S2', label: 'Speaker 2 IRI', default: 'ex:humanFEO065' }
        ],
        output_variables: [{
            name: 'overlapCount',
            label: 'Number of Overlapping Utterances'
        }]
    }
};



export function getCQRegistry() {
    return cqRegistry;
}
