import re

with open('/home/kelseyrook/Documents/GitHub/dialogueOnt/src/ontology/dido-edit.ttl', 'r') as f:
    content = f.read()

# Fix Utterance
content = content.replace(
'''                           [ rdf:type owl:Restriction ;
                             owl:onProperty sio:SIO_000291 ;
                             owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;
                             owl:onClass :DialogueActAnnotation
                           ] ,''',
'''                           [ rdf:type owl:Restriction ;
                             owl:onProperty sio:SIO_000292 ;
                             owl:someValuesFrom :DialogueActAnnotation
                           ] ,'''
)

# Fix DialogueActAnnotation
content = content.replace(
'''                                       [ rdf:type owl:Restriction ;
                                         owl:onProperty sio:SIO_000292 ;
                                         owl:minQualifiedCardinality "1"^^xsd:nonNegativeInteger ;
                                         owl:onClass :Utterance
                                       ] ;''',
'''                                       [ rdf:type owl:Restriction ;
                                         owl:onProperty sio:SIO_000291 ;
                                         owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ;
                                         owl:onClass :Utterance
                                       ] ;'''
)

# Fix DialogueAct and add hasAddressee
content = content.replace(
'''###  http://purl.org/dido#DialogueAct
:DialogueAct rdf:type owl:Class ;
             rdfs:subClassOf sio:SIO_000614 ,
                             [ rdf:type owl:Restriction ;
                               owl:onProperty sio:SIO_000226 ;
                               owl:someValuesFrom :Utterance
                             ] ;''',
'''###  http://purl.org/dido#hasAddressee
:hasAddressee rdf:type owl:ObjectProperty .

###  http://purl.org/dido#DialogueAct
:DialogueAct rdf:type owl:Class ;
             rdfs:subClassOf sio:SIO_000614 ,
                             [ rdf:type owl:Restriction ;
                               owl:onProperty sio:SIO_000226 ;
                               owl:someValuesFrom :Utterance
                             ] ,
                             [ rdf:type owl:Restriction ;
                               owl:onProperty :hasAddressee ;
                               owl:someValuesFrom :Interlocutor
                             ] ;'''
)

# Add DiscourseRelation and DiscourseRelationAnnotation
discourse_add = '''
###  http://purl.org/dido#DiscourseRelation
:DiscourseRelation rdf:type owl:Class ;
                   rdfs:subClassOf sio:SIO_000006 ,
                                   [ rdf:type owl:Restriction ;
                                     owl:onProperty sio:SIO_000291 ;
                                     owl:someValuesFrom :Utterance
                                   ] ,
                                   [ rdf:type owl:Restriction ;
                                     owl:onProperty sio:SIO_000253 ;
                                     owl:someValuesFrom :Utterance
                                   ] ;
                   rdfs:label "discourse relation" .

###  http://purl.org/dido#DiscourseRelationAnnotation
:DiscourseRelationAnnotation rdf:type owl:Class ;
                             rdfs:subClassOf powla:Terminal ,
                                             [ rdf:type owl:Restriction ;
                                               owl:onProperty sio:SIO_000332 ;
                                               owl:someValuesFrom :DiscourseRelation
                                             ] ;
                             rdfs:label "discourse relation annotation" .
'''
# Append them before ###  http://purl.org/dido#Interlocutor
content = content.replace('###  http://purl.org/dido#Interlocutor', discourse_add + '\n###  http://purl.org/dido#Interlocutor')

with open('/home/kelseyrook/Documents/GitHub/dialogueOnt/src/ontology/dido-edit.ttl', 'w') as f:
    f.write(content)
