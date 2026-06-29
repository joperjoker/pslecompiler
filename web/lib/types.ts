export type Option = {
  label: string;
  text: string;
  is_correct: boolean;
  rationale: string;
  misconception?: string | null;
};

export type Question = {
  qid: string;
  stem: string;
  subject: string;
  syllabus_version?: string;
  theme?: string | null;
  cognitive_level?: string | null;
  difficulty_band?: string | null;
  status?: string;
  provenance?: string;
  options: Option[];
  learning_outcomes?: string[];
  concepts: string[];
};
