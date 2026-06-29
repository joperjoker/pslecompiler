// Neo4j schema for the PSLE second-brain.
// Run this ONCE against your AuraDB instance before loading data
// (data/artifacts/<name>/load.cypher).
//
// Requires Neo4j 5.13+ for vector indexes (AuraDB Free qualifies).

// --- Uniqueness constraints (also create backing indexes) -------------------
CREATE CONSTRAINT subject_uid       IF NOT EXISTS FOR (n:Subject)         REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT syllabus_uid      IF NOT EXISTS FOR (n:SyllabusVersion) REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT theme_uid         IF NOT EXISTS FOR (n:Theme)           REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT topic_uid         IF NOT EXISTS FOR (n:Topic)           REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT subtopic_uid      IF NOT EXISTS FOR (n:SubTopic)        REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT lo_uid            IF NOT EXISTS FOR (n:LearningOutcome) REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT concept_uid       IF NOT EXISTS FOR (n:Concept)         REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT term_uid          IF NOT EXISTS FOR (n:Term)            REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT skill_uid         IF NOT EXISTS FOR (n:Skill)           REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT misconception_uid IF NOT EXISTS FOR (n:Misconception)   REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT distractor_uid    IF NOT EXISTS FOR (n:Distractor)      REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT wiki_uid          IF NOT EXISTS FOR (n:WikiArticle)     REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT community_uid     IF NOT EXISTS FOR (n:Community)        REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT paper_uid         IF NOT EXISTS FOR (n:Paper)            REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT question_uid      IF NOT EXISTS FOR (n:Question)         REQUIRE n.uid IS UNIQUE;
CREATE CONSTRAINT option_uid        IF NOT EXISTS FOR (n:Option)           REQUIRE n.uid IS UNIQUE;

// --- Lookup indexes for the structured filter -------------------------------
CREATE INDEX lo_subject_version IF NOT EXISTS
  FOR (n:LearningOutcome) ON (n.subject, n.syllabus_version);
CREATE INDEX lo_cognitive IF NOT EXISTS
  FOR (n:LearningOutcome) ON (n.cognitive_level);
CREATE INDEX concept_subject IF NOT EXISTS
  FOR (n:Concept) ON (n.subject);
CREATE INDEX question_subject_version IF NOT EXISTS
  FOR (n:Question) ON (n.subject, n.syllabus_version);
CREATE INDEX question_status IF NOT EXISTS
  FOR (n:Question) ON (n.status);

// --- Vector indexes (cosine). Dimension must match the embedding model. -----
// BGE-M3 = 1024. Change if you use a different model. Safe to create even
// before embeddings exist; they are used once nodes carry an `embedding`.
CREATE VECTOR INDEX lo_embedding IF NOT EXISTS
  FOR (n:LearningOutcome) ON (n.embedding)
  OPTIONS { indexConfig: { `vector.dimensions`: 1024, `vector.similarity_function`: 'cosine' } };
CREATE VECTOR INDEX concept_embedding IF NOT EXISTS
  FOR (n:Concept) ON (n.embedding)
  OPTIONS { indexConfig: { `vector.dimensions`: 1024, `vector.similarity_function`: 'cosine' } };
CREATE VECTOR INDEX wiki_embedding IF NOT EXISTS
  FOR (n:WikiArticle) ON (n.embedding)
  OPTIONS { indexConfig: { `vector.dimensions`: 1024, `vector.similarity_function`: 'cosine' } };
CREATE VECTOR INDEX community_embedding IF NOT EXISTS
  FOR (n:Community) ON (n.embedding)
  OPTIONS { indexConfig: { `vector.dimensions`: 1024, `vector.similarity_function`: 'cosine' } };
CREATE VECTOR INDEX question_embedding IF NOT EXISTS
  FOR (n:Question) ON (n.embedding)
  OPTIONS { indexConfig: { `vector.dimensions`: 1024, `vector.similarity_function`: 'cosine' } };
