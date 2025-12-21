# CyberThreat-Intelligence

RAG System for Cyber Threat monitoring

@authors: MJ.BAIM, A.ORKHIS

Ingestion Kafka + Zookeeper
on va avoir deux TOPICS

### Topics utilisés

raw-data : données brutes (pulses OTX non modifiés, enveloppés dans un message)
structured-data : documents normalisés prêts pour stockage SQL + embeddings

### Création des topics Kafka

bin/kafka-topics.sh --bootstrap-server localhost:9092
--create --topic raw-data --partitions 1 --replication-factor 1

bin/kafka-topics.sh --bootstrap-server localhost:9092
--create --topic structured-data --partitions 1 --replication-factor 1

#### Vérification :

bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

Vérifie aussi que

export OTX_API_KEY=VOTRE_CLE_API_OTX
VOTRE_CLE_API_OTX = voir sur AlienVault OTX API

### Data Ingestion (OTX → Kafka)

python otx_producer.py

Vérification :
bin/kafka-console-consumer.sh
--bootstrap-server localhost:9092
--topic raw-data
--from-beginning

### Data Transformation (Raw → Structured)

python otx_transformer.py

Vérification :
bin/kafka-console-consumer.sh
--bootstrap-server localhost:9092
--topic structured-data
--from-beginning

La pipeline se divise en deux :

### SQL Pipeline threats.db

Créer les tables en utilisant python init_db.py.
Utilise-le si c’est la première fois que tu exécutes le code, sinon tu as deux options :
soit supprimer la table qui apparaît dans ton répertoire,
soit réinitialiser la base.

python sql_consumer.py lie le topic Raw data à la table SQL et stocke les données

### La pipeline qui va nous servir :

python embedding_consumer.py

## Lancer Kafka

Zookeeper: 'bin/zookeeper-server-start.sh config/zookeeper.properties'
Kafka : 'bin/kafka-server-start.sh config/server.properties'
