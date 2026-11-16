// AI-assisted (Claude Code, 2026-11-16). Types of the LOCAL prototype export
// (scripts/publish/export_prototype.py). Every displayed value carries a status (DATA.md "결측 상태").

export type Status =
  | 'observed' | 'derived' | 'absent_in_text' | 'not_applicable' | 'not_scalar'
  | 'not_extracted' | 'unresolved' | 'not_in_corpus' | 'withheld';

export interface Field<T = number | null> { value: T; status: Status; reason?: string; spans?: number[][] }

export interface SideFields {
  prison_months: Field;
  suspension_months: Field;
  confinement_months: Field;
}

export interface SupremeAction { action: 'dismissed' | 'reversed_remanded' | 'reversed_transferred'; scope: string; supreme_id: string }

export interface Term { months: number; span: number[] }

export interface Defendant {
  id: string;
  appeal_basis: string | null;
  terms: { trial: Term[]; appeal: Term[] };
  fields: { trial: SideFields; appeal: SideFields; supreme_outcome: Field<SupremeAction[] | null> };
}

export interface DocHead { id: string; case_no: string; court: string; date: string; display_ok: boolean }

export interface Pair {
  id: string;
  trial: DocHead;
  appeal: DocHead;
  link_status: string;
  defendants: Defendant[];
  unresolved_count: number;
  supreme: Field<SupremeAction[] | null>;
  k1: string;
  k2: string;
}

export interface Cue { span: number[]; text: string | null }
export interface Ground extends Cue { label: string; origin: string; in_summary: boolean }
export interface Disposition extends Cue { type: 'accepted' | 'rejected' | 'not_reached' | 'reversal'; target: string | null; basis: string | null }
export interface Article {
  law: string; article: string; title: string | null; version_date: string | null;
  kb_status: 'contextual' | 'not_in_corpus'; first_paragraph: string | null;
}
export interface Step { step: string; label: string; articles: Article[] }
export interface Factor extends Cue { factor: string; label: string; polarity: 'mitigating' | 'aggravating' | 'unstated' }

export interface Appeal {
  case_no: string;
  display_ok: boolean;
  grounds: Ground[];
  dispositions: Disposition[];
  ex_officio: Cue[];
  steps: Step[];
  steps_status: Status;
  factors: Factor[];
  factor_status: Status;
  statute_change: { removed: string[]; added: string[]; status: string } | null;
}

export interface Section { title: string; start: number; end: number }
export interface DocumentText {
  case_no: string; court: string; date: string; display_ok: boolean; length: number;
  sections: Section[];
  text: string | null; // null = withheld (unmasked names in the only available copy)
}

export interface Dataset {
  meta: { run: string; note: string; pairs: number; appeals: number; k1_counts: Record<string, number>; k2_counts: Record<string, number> };
  pairs: Pair[];
  appeals: Record<string, Appeal>;
  documents: Record<string, DocumentText>;
}

export const MAX_MONTHS = 240;
