import re

with open('/home/kelseyrook/Documents/GitHub/dialogueOnt/src/ontology/dido-edit.ttl', 'r') as f:
    content = f.read()

# Update DialogueActAnnotation
content = content.replace(
'''###  http://purl.org/dido#DialogueActAnnotation
:DialogueActAnnotation rdf:type owl:Class ;
                       rdfs:subClassOf powla:Terminal ,
                                       [ rdf:type owl:Restriction ;
                                         owl:onProperty sio:SIO_000332 ;
                                         owl:someValuesFrom :DialogueAct
                                       ] ,
                                       [ rdf:type owl:Restriction ;
                                         owl:onProperty sio:SIO_000291 ;
                                         owl:minQualifiedCardinality "1"^^xsd:nonNegativeInteger ;
                                         owl:onClass :Utterance
                                       ] ;''',
'''###  http://purl.org/dido#DialogueActAnnotation
:DialogueActAnnotation rdf:type owl:Class ;
                       rdfs:subClassOf powla:Terminal ,
                                       [ rdf:type owl:Restriction ;
                                         owl:onProperty sio:SIO_000332 ;
                                         owl:someValuesFrom :DialogueAct
                                       ] ,
                                       [ rdf:type owl:Restriction ;
                                         owl:onProperty sio:SIO_000292 ;
                                         owl:minQualifiedCardinality "1"^^xsd:nonNegativeInteger ;
                                         owl:onClass :Utterance
                                       ] ;'''
)

# Update DialogueAct
content = content.replace(
'''###  http://purl.org/dido#DialogueAct
:DialogueAct rdf:type owl:Class ;
             rdfs:subClassOf sio:SIO_000614 ,
                             [ rdf:type owl:Restriction ;
                               owl:onProperty sio:SIO_000011 ;
                               owl:someValuesFrom :Utterance
                             ] ;''',
'''###  http://purl.org/dido#DialogueAct
:DialogueAct rdf:type owl:Class ;
             rdfs:subClassOf sio:SIO_000614 ,
                             [ rdf:type owl:Restriction ;
                               owl:onProperty sio:SIO_000226 ;
                               owl:someValuesFrom :Utterance
                             ] ;'''
)

# Update Utterance
content = content.replace(
'''###  http://purl.org/dido#Utterance
:Utterance rdf:type owl:Class ;
           rdfs:subClassOf sio:SIO_000006 ,
                           [ rdf:type owl:Restriction ;
                             owl:onProperty sio:SIO_000008 ;
                             owl:someValuesFrom :DialogueAct
                           ] ,''',
'''###  http://purl.org/dido#Utterance
:Utterance rdf:type owl:Class ;
           rdfs:subClassOf sio:SIO_000006 , powla:Nonterminal ,
                           [ rdf:type owl:Restriction ;
                             owl:onProperty sio:SIO_000225 ;
                             owl:someValuesFrom :DialogueAct
                           ] ,'''
)

content = content.replace(
'''                           [ rdf:type owl:Restriction ;
                             owl:onProperty sio:SIO_000292 ;
                             owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;
                             owl:onClass :DialogueActAnnotation
                           ] ,''',
'''                           [ rdf:type owl:Restriction ;
                             owl:onProperty sio:SIO_000291 ;
                             owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;
                             owl:onClass :DialogueActAnnotation
                           ] ,'''
)

with open('/home/kelseyrook/Documents/GitHub/dialogueOnt/src/ontology/dido-edit.ttl', 'w') as f:
    f.write(content)
