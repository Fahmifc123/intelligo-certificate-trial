// Form Data Types
export interface CertificateFormData {
  name: string;
  email: string;
  project_title: string;
  program_title: string;
  start_date: string;
  end_date: string;
  social_link: string;
}

// API Response Types
export interface CertificateResponse {
  success: boolean;
  certificate_url?: string;
  certificate_id?: string;
  message?: string;
  error?: string;
  ocr_text?: string;
  ai_validation?: boolean;
  keywords_found?: string[];
  email?: string;
  name?: string;
  validation?: {
    ocr_valid: boolean;
    ai_valid: boolean;
  };
  details?: {
    ocr_valid: boolean;
    ai_valid: boolean;
    keywords_found: string[];
  };
}

// Component Props Types
export interface CertificateFormProps {
  formData: CertificateFormData;
  file: File | null;
  screenshot: File | null;
  onInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onScreenshotChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
}

export interface SuccessStateProps {
  certificateUrl: string;
  onReset: () => void;
}

export interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export interface Requirement {
  icon: React.ComponentType<{ className?: string }>;
  text: string;
}
