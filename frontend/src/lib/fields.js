import { Home, Shield, Landmark, FileText } from "lucide-react";

export const FIELD_LABELS = {
  tenant: "Tenant",
  owner: "Owner",
  monthly_rent: "Monthly rent",
  security_deposit: "Security deposit",
  agreement_expiry: "Agreement expiry",
  notice_period_months: "Notice period (months)",
  policy_holder: "Policy holder",
  insured_asset: "Insured asset",
  provider: "Provider",
  coverage_amount: "Coverage amount",
  expiry_date: "Expiry date",
  borrower: "Borrower",
  loan_amount: "Loan amount",
  interest_rate_pct: "Interest rate (%)",
  repayment_period_months: "Repayment period (months)",
  next_important_date: "Next important date",
};

// One of the logo's three document-card colors per document type.
export const DOC_TYPES = {
  rent_agreement: {
    label: "Rent agreement",
    Icon: Home,
    tile: "bg-brand/15 text-brand-light",
    chip: "border-brand/30 bg-brand/15 text-brand-light",
  },
  insurance: {
    label: "Insurance",
    Icon: Shield,
    tile: "bg-mint/10 text-mint",
    chip: "border-mint/30 bg-mint/10 text-mint",
  },
  loan_agreement: {
    label: "Loan",
    Icon: Landmark,
    tile: "bg-violet/15 text-violet-light",
    chip: "border-violet/30 bg-violet/15 text-violet-light",
  },
};

export const FALLBACK_DOC_TYPE = {
  label: "Document",
  Icon: FileText,
  tile: "bg-raised text-inkFaint",
  chip: "border-line bg-raised text-inkFaint",
};

export function docTypeMeta(type) {
  return DOC_TYPES[type] || FALLBACK_DOC_TYPE;
}

export function isBlank(value) {
  return value === null || value === undefined || value === "";
}

// Field entries minus the internal document_type key.
export function fieldEntries(fields) {
  return Object.entries(fields || {}).filter(([key]) => key !== "document_type");
}
