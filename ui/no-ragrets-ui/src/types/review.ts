/**
 * Types for the Rubric Review system
 */

export type RubricName = 
  | 'methodology'
  | 'reproducibility'
  | 'rigor'
  | 'data'
  | 'presentation'
  | 'references';

export interface ReviewMetadata {
  provider: string;
  model: string;
}

export interface ReviewResponse {
  rubric_name?: string; // Optional - may be returned as just 'rubric' for some endpoints
  rubric?: string; // Alternative field name
  review?: string; // Response text from figure/table reviews
  response?: string; // Response text from text reviews
  metadata?: ReviewMetadata;
}

export interface RubricOption {
  value: RubricName;
  label: string;
  description: string;
}

export const RUBRIC_OPTIONS: RubricOption[] = [
  {
    value: 'methodology',
    label: 'Methodology',
    description: 'Research design, experimental approach, validation methods'
  },
  {
    value: 'reproducibility',
    label: 'Reproducibility',
    description: 'Code availability, data sharing, procedural details'
  },
  {
    value: 'rigor',
    label: 'Rigor',
    description: 'Statistical analysis, controls, bias mitigation'
  },
  {
    value: 'data',
    label: 'Data',
    description: 'Dataset quality, labeling, metrics, documentation'
  },
  {
    value: 'presentation',
    label: 'Presentation',
    description: 'Clarity, organization, figures, writing quality'
  },
  {
    value: 'references',
    label: 'References',
    description: 'Citation completeness, literature coverage, attribution'
  }
];
