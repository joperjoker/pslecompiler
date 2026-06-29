export type Block = {
  type: "text" | "image" | "table";
  text?: string;
  src?: string;
  alt?: string;
  header?: string[];
  rows?: string[][];
};

export type Option = {
  label: string;
  text: string;
  image?: string | null;
  is_correct: boolean;
  rationale: string;
  misconception?: string | null;
};

export type Question = {
  qid: string;
  stem: string;
  stem_blocks?: Block[];
  hint?: string;
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
